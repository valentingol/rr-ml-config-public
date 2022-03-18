import json
import os
import scipy.stats as stats
import numpy as np


class Metrics:
    @staticmethod
    def exponential_l2(ground_truth, predictions):
        return ((np.exp(ground_truth) - predictions)**2).mean()

    @staticmethod
    def square_root_l2(ground_truth, predictions):
        return ((np.sqrt(1+ground_truth) - predictions)**2).mean()


def create_data(data_config):
    mu = data_config.generation.mean
    sigma = data_config.generation.variance
    train = stats.truncnorm((-1 - mu) / sigma, (1 - mu) / sigma, loc=mu, scale=sigma).rvs(data_config.train.size)
    test = stats.truncnorm((-1 - mu) / sigma, (1 - mu) / sigma, loc=mu, scale=sigma).rvs(data_config.test.size)
    return train, test


def create_and_train_model(model_config, train_samples):
    def model(x):
        if model_config.type == "linear":
            return 1 + x*model_config.param1 + x*model_config.param2 + x*model_config.param3
        elif model_config.type == "polynomial":
            return 1 + x*model_config.param1 + np.power(x, 2)*model_config.param2 + np.power(x, 3)*model_config.param3
    _ = train_samples  # added train samples for reference, but they're not actually used here
    return model


def test_model_and_return_metrics(model, test_samples, metrics):
    predictions = model(test_samples)
    return {metric: getattr(Metrics, metrics[metric])(test_samples, predictions)
            for metric in metrics}


def log_experiment(config, metrics):
    exp_dir = os.path.join("log", config.name)
    if not os.path.exists(exp_dir):
        os.makedirs(exp_dir)
    run_dir = os.path.join(exp_dir, f"run_{len(os.listdir(exp_dir))}")
    os.makedirs(run_dir)
    config.save(os.path.join(run_dir, "config_save.yaml"))
    json.dump(metrics, open(os.path.join(run_dir, "metrics.json"), 'w'))
