# -*- coding: utf-8 -*-

from neuralforecast.utils import AirPassengersDF
from ray import tune
from neuralforecast.auto import AutoNHITS
from ray.tune.search.hyperopt import HyperOptSearch
from neuralforecast.losses.pytorch import MAE
from neuralforecast.auto import AutoNHITS
from neuralforecast import NeuralForecast
import pandas as pd
import matplotlib.pyplot as plt
import time


file = './wg_iotp_sensors.csv'
ds = "Asia/Singapore Time"
y = "Data"
Y_df = pd.read_csv(file)[[ds, y]].rename(columns={ds: "ds", y: "y"})
Y_df = Y_df[Y_df.reset_index().index % 180 == 0]

Y_df["ds"] = pd.to_datetime(Y_df["ds"], errors='coerce')
Y_df = Y_df.set_index('ds').tz_convert('UTC').tz_localize(None).reset_index()
Y_df = Y_df.drop_duplicates()
Y_df["unique_id"] = ['123' for _ in range(len(Y_df))]
Y_train_df = Y_df[Y_df.ds<='2024-08-30'] # 218k train
Y_train_df = Y_train_df[Y_train_df.ds>'2024-08-21']
Y_test_df = Y_df[Y_df.ds>'2024-08-30'] # 25k test
Y_test_df = Y_test_df[Y_test_df.ds<='2024-08-31']
freq = 'h'


nhits_config = AutoNHITS.get_default_config(h = 12, backend="ray")                      # Extract the default hyperparameter settings
nhits_config["random_seed"] = tune.randint(1, 10)                                       # Random seed
nhits_config["n_pool_kernel_size"] = tune.choice([[2, 2, 2], [16, 8, 1]])               # MaxPool's Kernelsize

nhits_config = {
    "max_steps": 100,                                                         # Number of SGD steps
    "input_size": 24,                                                         # Size of input window
    "learning_rate": tune.loguniform(1e-5, 1e-1),                             # Initial Learning rate
    "n_pool_kernel_size": tune.choice([[2, 2, 2], [16, 8, 1]]),               # MaxPool's Kernelsize
    "n_freq_downsample": tune.choice([[168, 24, 1], [24, 12, 1], [1, 1, 1]]), # Interpolation expressivity ratios
    "val_check_steps": 50,                                                    # Compute validation every 50 steps
    "random_seed": tune.randint(1, 10),                                       # Random seed
}
try:
    nf = None
    nf = NeuralForecast.load(path='./models/AutoNHITS/')
except Exception:
    print("No saved model found. Training new model.")


if nf:
    print("Loaded saved model")
else:
    # train new model
    model = AutoNHITS(
        h=12,
        loss=MAE(),
        config=nhits_config,
        search_alg=HyperOptSearch(),
        backend='ray',
        num_samples=10
    )

    nf = NeuralForecast(models=[model], freq=freq)
    start0 = time.process_time()
    nf.fit(df=Y_train_df, val_size=24)
    nf_auto_time = time.process_time() - start0
    nf.save(path='./models/AutoNHITS/',
            model_index=None, 
            overwrite=True,
            save_dataset=False)


    results = nf.models[0].results.get_dataframe()
    with open('./models/AutoNHITS/hyperparams.txt', 'w') as f:
        f.write("Optimal parameters\n")
        f.write(str(results.head()))
        f.write(f"\n\n{nf_auto_time=} seconds")

    print("Optimal parameters")
    print(results.head())
    print(f"{nf_auto_time=} seconds")

input("\n======= press enter to continue =======\n")


cv_df = nf.cross_validation(
    df=Y_train_df,
    n_windows=3,
)
print(cv_df)
def plot_cv(df, df_cv, uid, fname, last_n=24 * 14):
    cutoffs = df_cv.query('unique_id == @uid')['cutoff'].unique()
    fig, ax = plt.subplots(nrows=len(cutoffs), ncols=1, figsize=(14, 6), gridspec_kw=dict(hspace=0.8))
    for cutoff, axi in zip(cutoffs, ax.flat):
        df.query('unique_id == @uid').tail(last_n).set_index('ds').plot(ax=axi, title=uid, y='y')
        df_cv.query('unique_id == @uid & cutoff == @cutoff').set_index('ds').plot(ax=axi, title=uid, y='AutoNHITS')
    fig.savefig(fname, bbox_inches='tight')
    plt.close()


plot_cv(Y_train_df, cv_df, '123', './models/AutoNHITS/cross_validation__predictions.png')

input("\n======= press enter to continue =======\n")



Y_hat_df = nf.predict()
Y_hat_df = Y_hat_df.reset_index()
print(Y_hat_df)

fig, ax = plt.subplots(1, 1, figsize = (16, 7))
Y_hat_df = Y_test_df.merge(Y_hat_df, how='left', on=['unique_id', 'ds'])
plot_df = pd.concat([Y_train_df, Y_hat_df]).set_index('ds')

columns = ['y', 'AutoNHITS']
plot_df[columns].plot(ax=ax, linewidth=1)
print(plot_df)

ax.set_title("IOTP Sensors", fontsize=22)
ax.set_ylabel("Temperature", fontsize=20)
ax.set_xlabel('Timestamp [t]', fontsize=20)
ax.legend(prop={'size': 15})
ax.grid()

fig.savefig('./models/AutoNHITS/forecast.png', bbox_inches='tight')
plt.show()