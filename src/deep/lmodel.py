import time, random
import jax, optax
import jax.numpy as jnp
import haiku as hk
from typing import NamedTuple

#=================================
class DownBlock(hk.Module):
    #Default Keras BatchNorm Settings
    sBN_config = {
        "decay_rate": 0.99,
        "eps": 1e-3,
        "create_scale": True,
        "create_offset": True}

    def __init__(self, in_size, output_channels=1, prefix=""):
        super().__init__(name=f"DownBlock_{in_size}")
        self.mInSize = in_size
        self.mOutSize = in_size//2

        self.mConv1 = hk.Conv2D(
            output_channels=output_channels,
            kernel_shape=3, name=f"{prefix}conv1_{in_size}", padding="SAME")
        self.mConv2 = hk.Conv2D(
            output_channels=output_channels,
            kernel_shape=3, name=f"{prefix}conv2_{in_size}", padding="SAME")
        self.mBatchNorm = hk.BatchNorm(name=f"{prefix}bn_{in_size}", **self.sBN_config)

    def __call__(self, inputs: jnp.ndarray, is_training: bool):
        out = inputs
        out = self.mConv1(out)
        out = self.mConv2(out)
        out = self.mBatchNorm(out, is_training)
        out = jax.nn.relu(out)
        out = hk.max_pool(out, window_shape=1, strides=2, padding="SAME")
        return out

#=================================
class LModel(hk.Module):
    def __init__(self, total_size=128):
        super().__init__(name=f"LModel_{total_size}")
        self.mBlocks = [DownBlock(size) for size in (128, 64, 32, 16)]
        self.mBlocks.append(DownBlock(4, output_channels=2))
        self.mFinalLinear = hk.Linear(5, name="fin_lin")
        self.mRngKey = jax.random.PRNGKey(179);

    def __call__(self, inputs: jnp.ndarray, is_training: bool):
        out = inputs
        for blk in self.mBlocks:
            out = blk(out, is_training)
        out = out.reshape(out.shape[0], 32)
        if is_training:
            self.mRngKey, key = jax.random.split(self.mRngKey)
            out = hk.dropout(key, .1, out)
        out = self.mFinalLinear(out)
        return out

#=================================
class EvalEnv:
    def __init__(self, is_training):
        self.mForward = hk.transform_with_state(self.__forward)
        self.mIsTraining = is_training

    @staticmethod
    def __forward(input_data, is_training):
        net = LModel()
        out = net(input_data, is_training)
        return out

    def isTraining(self):
        return self.mIsTraining

    def _initState(self, rng_key=42):
        x_train = jnp.zeros((1, 128, 128, 1), float)
        params, state = self.mForward.init(
            jax.random.PRNGKey(rng_key),
            x_train,
            is_training=self.mIsTraining)
        return params, state

    def apply(self, params, state, input_data, is_training=None):
        if is_training is None:
            is_training = self.mIsTraining
        assert self.mIsTraining or not is_training
        if len(input_data.shape) == 2:
            assert input_data.shape == (128, 128)
            input_data = input_data.reshape(1, 128, 128)
        return self.mForward.apply(params, state, None, input_data,
            is_training=is_training)

#=================================
class TrainState(NamedTuple):
    params: hk.Params
    state: hk.State
    opt_state: optax.OptState

#=================================
def iterPortions(train_data, portion):
    for idx in range(0, len(train_data), portion):
        gen = jnp.array([it for it, _ in train_data[idx : idx + portion]])
        target = jnp.array([it for _, it in train_data[idx : idx + portion]])
        yield gen, target

#=================================
def _activateLearningFunctions(forward, opt, loss_coeff):
    def loss(params, state, gen_target, is_training):
        gen, target = gen_target
        result, state = forward.apply(params, state, None, gen,
            is_training=is_training)
        error = (target - result) # * loss_coeff
        loss_value = jnp.linalg.norm(error, axis=1).sum()
        return loss_value, state

    grad_f = jax.grad(loss, has_aux=True)

    def train_step(train_state: TrainState, gen, target):
        params, state, opt_state = train_state
        grads, new_state = grad_f(params, state, (gen, target), True)
        updates, new_opt_state = opt.update(grads, opt_state)
        new_params = optax.apply_updates(params, updates)
        return TrainState(new_params, new_state, new_opt_state)

    def ema_update(train_state: TrainState, acc_state: TrainState):
        acc_params = optax.incremental_update(
            train_state[0], acc_state[0], step_size=3e-1)
        return TrainState(acc_params, train_state[1], None)

    return loss, jax.jit(train_step), jax.jit(ema_update)

#=================================
class LearningEnv:

    sLossCoeff = jnp.array([1., 1., 1., .01, .1], float)

    def __init__(self):
        self.mEvalEnv = EvalEnv(True)
        #Default Keras RMSprop Settings
        self.mOpt = optax.rmsprop(learning_rate=1e-3, eps=1e-07)
        self.mLossF = None
        self.mTrainStepF = None
        self.mOptUpdateF = None
        self.mLossF, self.mTrainStepF, self.mOptUpdateF = (
            _activateLearningFunctions(self.mEvalEnv.mForward,
                self.mOpt, self.sLossCoeff))

    def initialState(self, rng_key=42) -> TrainState:
        params, state = self.mEvalEnv._initState(rng_key)
        opt_state = self.mOpt.init(params)
        return TrainState(params, state, opt_state)

    def doTrainStep(self,train_state, gen, target):
        return self.mTrainStepF(train_state, gen, target)

    def doOptUpdate(self, train_state, acc_state):
        return self.mOptUpdateF(train_state, acc_state)

    def accuracy(self, train_state, gen, target):
        params, state, _ = train_state

        result, _ = self.mEvalEnv.apply(params, state, gen, False)
        error = (target - result) # * self.sLossCoeff
        return jnp.linalg.norm(error, axis=1)

    def meanLoss(self, acc_state, train_data, portion=100):
        seq = []
        for gen, target in iterPortions(train_data, portion):
            loss_portion = self.accuracy(acc_state, gen, target)
            seq.append(loss_portion)
        return jnp.mean(jnp.concatenate(seq), axis=0)

#=================================
def doLearn(train_data, epochs, portion=30, eportion=1):
    l_env = LearningEnv()
    r_h = random.Random(179)
    train_state = l_env.initialState()
    acc_state = TrainState(train_state.params, train_state.state, None)

    mean_loss = l_env.meanLoss(acc_state, train_data)
    print("Loss: {:0.4f}".format(mean_loss))
    print("Training will begin...")

    total_start = eport_start = time.time()
    for epoch in range(1, epochs + 1):
        start_time = time.time()

        for gen, target in iterPortions(train_data, portion):
            train_state = l_env.doTrainStep(train_state, gen, target)
        acc_state = l_env.doOptUpdate(train_state, acc_state)
        epoch_time = time.time() - start_time

        if epoch % eportion == 0:
            r_h.shuffle(train_data)
            mean_loss = l_env.meanLoss(acc_state, train_data)
            print("Loss: {:0.4f}".format(mean_loss))
            print("Epoch {} in {:0.2f} sec | last {}: {:0.2f} sec | total: {:0.2f} min: ".format(
                epoch, epoch_time, eportion, start_time - eport_start, (start_time - total_start)/60))
            eport_start = start_time
    return train_state.params
