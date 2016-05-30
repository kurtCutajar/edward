import numpy as np
import tensorflow as tf

from edward.util import logit

# template
def predict(self, xs, zs):
    """
    Parameters
    ----------
    xs : Data
        N data points.
    zs : tf.Tensor
        S x d matrix.

    Returns
    -------
    tf.Tensor
        N x S matrix where entry (i, j) is the predicted
        value for the ith data point given the jth set of latent
        variables.

        For supervised tasks, the predicted value is the mean of the
        output's likelihood given features from the ith data point and
        jth set of latent variables:
            + Binary classification. The probability of the success
            label.
            + Multi-class classification. The probability of each
            label, with the entire output of shape N x S x K.
            (one-shot or label representation downstream?)
            + Regression. The mean response.
        For unsupervised, the predicted value is the log-likelihood
        evaluated at the ith data point given jth set of latent
        variables.
    """
    pass

# TODO 3
def sample_prior():
    pass

def sample_lik():
    pass

# TODO default to grabbing session from environment if it exists
# to do this, inference will need to globally define the session
def evaluate(metrics, model, variational, data, sess=tf.Session()):
    """
    Parameters
    ----------
    metric : list or str
        List of metrics or a single metric.

    Returns
    -------
    list or float
        A list of evaluations or a single evaluation.
    """
    # Monte Carlo estimate the mean of the posterior predictive:
    # 1. Sample a batch of latent variables from posterior
    xs = data.data
    n_minibatch = 100
    zs, samples = variational.sample(xs, size=n_minibatch)
    feed_dict = variational.np_sample(samples, n_minibatch, sess=sess)
    # 2. Form a set of predictions for each sample of latent variables
    y_pred_zs = model.predict(xs, zs)
    # 3. Average over set of predictions
    y_pred = tf.reduce_mean(y_pred_zs, 1)
    # TODO
    y_true = data.data[:, 0]

    # Evaluate y_pred according to y_true for all metrics.
    evaluations = []
    if isinstance(metrics, str):
        metrics = [metrics]

    for metric in metrics:
        if metric == 'accuracy' or 'crossentropy':
            # automate binary or sparse cat depending on max(y_true)
            support = sess.run(tf.maximum(y_true))
            if support <= 1:
                metric = 'binary_' + metric
            else:
                metric = 'sparse_categorical_' + metric

        if metric == 'binary_accuracy':
            evaluations += [sess.run(binary_accuracy(y_true, y_pred), feed_dict)]
        elif metric == 'categorical_accuracy':
            evaluations += [sess.run(categorical_accuracy(y_true, y_pred), feed_dict)]
        elif metric == 'sparse_categorical_accuracy':
            evaluations += [sess.run(sparse_categorical_accuracy(y_true, y_pred), feed_dict)]
        elif metric == 'log_loss' or metric == 'binary_crossentropy':
            evaluations += [sess.run(binary_crossentropy(y_true, y_pred), feed_dict)]
        elif metric == 'categorical_crossentropy':
            evaluations += [sess.run(categorical_crossentropy(y_true, y_pred), feed_dict)]
        elif metric == 'sparse_categorical_crossentropy':
            evaluations += [sess.run(sparse_categorical_crossentropy(y_true, y_pred), feed_dict)]
        elif metric == 'hinge':
            evaluations += [sess.run(hinge(y_true, y_pred), feed_dict)]
        elif metric == 'squared_hinge':
            evaluations += [sess.run(squared_hinge(y_true, y_pred), feed_dict)]
        elif metric == 'mse' or metric == 'MSE' or \
             metric == 'mean_squared_error':
            evaluations += [sess.run(mean_squared_error(y_true, y_pred), feed_dict)]
        elif metric == 'mae' or metric == 'MAE' or \
             metric == 'mean_absolute_error':
            evaluations += [sess.run(mean_absolute_error(y_true, y_pred), feed_dict)]
        elif metric == 'mape' or metric == 'MAPE' or \
             metric == 'mean_absolute_percentage_error':
            evaluations += [sess.run(mean_absolute_percentage_error(y_true, y_pred), feed_dict)]
        elif metric == 'msle' or metric == 'MSLE' or \
             metric == 'mean_squared_logarithmic_error':
            evaluations += [sess.run(mean_squared_logarithmic_error(y_true, y_pred), feed_dict)]
        elif metric == 'poisson':
            evaluations += [sess.run(poisson(y_true, y_pred), feed_dict)]
        elif metric == 'cosine' or metric == 'cosine_proximity':
            evaluations += [sess.run(cosine_proximity(y_true, y_pred), feed_dict)]
        elif metric == 'log_lik' or metric == 'log_likelihood':
            evaluations += [sess.run(y_pred, feed_dict)]
        else:
            raise NotImplementedError()

    if len(evaluations) == 1:
        return evaluations[0]
    else:
        return evaluations

def cv_evaluate(metric, model, variational, data, sess=tf.Session()):
    """
    Cross-validated evaluation
    """
    # TODO it calls evaluate(), wrapped around importance sampling
    raise NotImplementedError()

def ppc(model, variational, data, T, size=100, sess=tf.Session()):
    """
    Posterior predictive check.
    (Rubin, 1984; Meng, 1994; Gelman, Meng, and Stern, 1996)

    It form an empirical distribution for the predictive discrepancy,
    p(T) = \int p(T(x) | z) p(z | x) dz
    by drawing replicated data sets xrep and calculating T(xrep) for
    each data set. Then it compares it to T(xobs).

    Parameters
    ----------
    model : Model
        model object must have a 'sample_lik' method, which takes xs,
        zs, size as input and returns replicated data set
    data : Data
        Observed data to check to.
    variational : Variational
        latent variable distribution q(z) to sample from. It is an
        approximation to the posterior, e.g., a variational
        approximation or an empirical distribution from MCMC samples.
    T : function
        Discrepancy function.
    size : int, optional
        number of replicated data sets
    sess : tf.Session, optional
        session used during inference

    Returns
    -------
    list
        List containing the reference distribution, which is a Numpy
        vector of size elements,
        (T(xrep^{1}, z^{1}), ..., T(xrep^{size}, z^{size}));
        and the realized discrepancy, which is a NumPy array of size
        elements,
        (T(x, z^{1}), ..., T(x, z^{size})).
    """
    # TODO
    xobs = sess.run(data.data) # TODO generalize to arbitrary data
    Txobs = T(xobs)
    N = len(xobs) # TODO len, or shape[0]

    # TODO
    # size in variational sample
    # whether the sample method requires sess
    zreps = latent.sample([size, 1], sess)
    xreps = [model.sample_likelihood(zrep, N) for zrep in zreps]
    Txreps = [T(xrep) for xrep in xreps]
    return Txobs, Txreps

# TODO maybe it should default to prior PC if variational is not given as
# input
def prior_predictive_check(model, data, T):
    """
    Prior predictive check.
    (Box, 1980)

    It form an empirical distribution for the predictive discrepancy,
    p(T) = \int p(T(x) | z) p(z) dz
    by drawing replicated data sets xrep and calculating T(xrep) for
    each data set. Then it compares it to T(xobs).

    Parameters
    ----------
    model : Model
        model object must have a 'sample_lik' method, which takes xs,
        zs, size as input and returns replicated data set.
        model object must have a 'sample_prior' method, which takes xs,
        zs, size as input and returns...
    data : Data
        Observed data to check to.
    T : function
        Discrepancy function.
    size : int, optional
        number of replicated data sets
    sess : tf.Session, optional
        session used during inference

    Returns
    -------
    list
        List containing the reference distribution, which is a Numpy
        vector of size elements,
        (T(xrep^{1}, z^{1}), ..., T(xrep^{size}, z^{size}));
        and the realized discrepancy, which is a NumPy array of size
        elements,
        (T(x, z^{1}), ..., T(x, z^{size})).
    """
    raise NotImplementedError()

# Classification metrics

def binary_accuracy(y_true, y_pred):
    """
    Binary prediction accuracy, also known as 0/1-loss.

    Parameters
    ----------
    y_true : tf.Tensor
        Tensor of 0s and 1s.
    y_pred : tf.Tensor
        Tensor of probabilities.
    """
    y_true = tf.cast(y_true, tf.float32)
    y_pred = tf.cast(tf.round(y_pred), tf.float32)
    return tf.reduce_mean(tf.cast(tf.equal(y_true, y_pred), tf.float32))

def categorical_accuracy(y_true, y_pred):
    """
    Multi-class prediction accuracy. One-hot representation for
    y_true.

    Parameters
    ----------
    y_true : tf.Tensor
        Tensor of 0s and 1s, where the outermost dimension of size K
        has only one 1 per row.
    y_pred : tf.Tensor
        Tensor of probabilities, with same shape as y_true.
        The outermost dimension denote the categorical probabilities for
        that data point per row.
    """
    y_true = tf.cast(tf.argmax(y_true, len(y_true.get_shape()) - 1), tf.float32)
    y_pred = tf.cast(tf.argmax(y_pred, len(y_pred.get_shape()) - 1), tf.float32)
    return tf.reduce_mean(tf.cast(tf.equal(y_true, y_pred), tf.float32))

def sparse_categorical_accuracy(y_true, y_pred):
    """
    Multi-class prediction accuracy. Label {0, 1, .., K-1}
    representation for y_true.

    Parameters
    ----------
    y_true : tf.Tensor
        Tensor of integers {0, 1, ..., K-1}.
    y_pred : tf.Tensor
        Tensor of probabilities, with shape (y_true.get_shape(), K).
        The outermost dimension are the categorical probabilities for
        that data point.
    """
    y_true = tf.cast(y_true, tf.float32)
    y_pred = tf.cast(tf.argmax(y_pred, len(y_pred.get_shape()) - 1), tf.float32)
    return tf.reduce_mean(tf.cast(tf.equal(y_true, y_pred), tf.float32))

def binary_crossentropy(y_true, y_pred):
    """
    Parameters
    ----------
    y_true : tf.Tensor
        Tensor of 0s and 1s.
    y_pred : tf.Tensor
        Tensor of probabilities.
    """
    y_true = tf.cast(y_true, tf.float32)
    y_pred = logit(tf.cast(y_pred, tf.float32))
    return tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(y_pred, y_true))

def categorical_crossentropy(y_true, y_pred):
    """
    Multi-class cross entropy. One-hot representation for y_true.

    Parameters
    ----------
    y_true : tf.Tensor
        Tensor of 0s and 1s, where the outermost dimension of size K
        has only one 1 per row.
    y_pred : tf.Tensor
        Tensor of probabilities, with same shape as y_true.
        The outermost dimension denote the categorical probabilities for
        that data point per row.
    """
    y_true = tf.cast(y_true, tf.float32)
    y_pred = logit(tf.cast(y_pred, tf.float32))
    return tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(y_pred, y_true))

def sparse_categorical_crossentropy(y_true, y_pred):
    """
    Multi-class cross entropy. Label {0, 1, .., K-1} representation
    for y_true.

    Parameters
    ----------
    y_true : tf.Tensor
        Tensor of integers {0, 1, ..., K-1}.
    y_pred : tf.Tensor
        Tensor of probabilities, with shape (y_true.get_shape(), K).
        The outermost dimension are the categorical probabilities for
        that data point.
    """
    y_true = tf.cast(y_true, tf.int32)
    y_pred = logit(tf.cast(y_pred, tf.float32))
    return tf.reduce_mean(tf.nn.sparse_softmax_cross_entropy_with_logits(y_pred, y_true))

def hinge(y_true, y_pred):
    """
    Parameters
    ----------
    y_true : tf.Tensor
        Tensor of 0s and 1s.
    y_pred : tf.Tensor
        Tensor of real value.
    """
    y_true = tf.cast(y_true, tf.float32)
    y_pred = tf.cast(y_pred, tf.float32)
    return tf.reduce_mean(tf.maximum(1.0 - y_true * y_pred, 0.0))

def squared_hinge(y_true, y_pred):
    """
    Parameters
    ----------
    y_true : tf.Tensor
        Tensor of 0s and 1s.
    y_pred : tf.Tensor
        Tensor of real value.
    """
    y_true = tf.cast(y_true, tf.float32)
    y_pred = tf.cast(y_pred, tf.float32)
    return tf.reduce_mean(tf.square(tf.maximum(1.0 - y_true * y_pred, 0.0)))

# Regression metrics

def mean_squared_error(y_true, y_pred):
    """
    Parameters
    ----------
    y_true : tf.Tensor
    y_pred : tf.Tensor
        Tensors of same shape and type.
    """
    return tf.reduce_mean(tf.square(y_pred - y_true))

def mean_absolute_error(y_true, y_pred):
    """
    Parameters
    ----------
    y_true : tf.Tensor
    y_pred : tf.Tensor
        Tensors of same shape and type.
    """
    return tf.reduce_mean(tf.abs(y_pred - y_true))

def mean_absolute_percentage_error(y_true, y_pred):
    """
    Parameters
    ----------
    y_true : tf.Tensor
    y_pred : tf.Tensor
        Tensors of same shape and type.
    """
    diff = tf.abs((y_true - y_pred) / tf.clip_by_value(tf.abs(y_true), 1e-8, np.inf))
    return 100.0 * tf.reduce_mean(diff)

def mean_squared_logarithmic_error(y_true, y_pred):
    """
    Parameters
    ----------
    y_true : tf.Tensor
    y_pred : tf.Tensor
        Tensors of same shape and type.
    """
    first_log = tf.log(tf.clip_by_value(y_pred, 1e-8, np.inf) + 1.0)
    second_log = tf.log(tf.clip_by_value(y_true, 1e-8, np.inf) + 1.0)
    return tf.reduce_mean(tf.square(first_log - second_log))

def poisson(y_true, y_pred):
    """
    Negative Poisson log-likelihood of data y_true given predictions
    y_pred (up to proportion).

    Parameters
    ----------
    y_true : tf.Tensor
    y_pred : tf.Tensor
        Tensors of same shape and type.
    """
    return tf.reduce_sum(y_pred - y_true * tf.log(y_pred + 1e-8))

def cosine_proximity(y_true, y_pred):
    """
    Cosine similarity of two vectors.

    Parameters
    ----------
    y_true : tf.Tensor
    y_pred : tf.Tensor
        Tensors of same shape and type.
    """
    y_true = tf.nn.l2_normalize(y_true, len(y_true.get_shape()) - 1)
    y_pred = tf.nn.l2_normalize(y_pred, len(y_pred.get_shape()) - 1)
    return tf.reduce_sum(y_true * y_pred)
