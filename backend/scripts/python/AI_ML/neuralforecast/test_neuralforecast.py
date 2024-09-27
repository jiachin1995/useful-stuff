# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
from prophet import Prophet
from neuralprophet import NeuralProphet 
from neuralforecast import NeuralForecast
from neuralforecast.models import NBEATS, NHITS
import time

def load_airpassengers():
    # source data using Neuralforecast example data
    from neuralforecast.utils import AirPassengersDF

    Y_df = AirPassengersDF
    Y_train_df = Y_df[Y_df.ds<='1959-12-31'] # 132 train
    Y_test_df = Y_df[Y_df.ds>'1959-12-31'] # 12 test
    freq = 'M'

    return Y_train_df, Y_test_df, freq

def load_sinwave():
    # source data using fake sin curve
    file = './fake_data_daily.csv'
    ds = "Asia/Singapore Time"
    y = "Data"
    Y_df = pd.read_csv(file)[[ds, y]].rename(columns={ds: "ds", y: "y"})
    Y_df["ds"] = pd.to_datetime(Y_df["ds"], errors='coerce')
    Y_df = Y_df.set_index('ds').tz_convert('UTC').tz_localize(None).reset_index()
    Y_df["unique_id"] = [123 for _ in range(len(Y_df))]
    Y_train_df = Y_df[Y_df.ds<='2024-11-26'] # 88 train
    Y_test_df = Y_df[Y_df.ds>'2024-11-26'] # 13 test
    freq = 'D'

    return Y_train_df, Y_test_df, freq

def load_iotp_sensors():
    """
    Warning! Sensor data does not work with neuralforecast. (too many rows)
    """
    # source data using 2 month sensor data
    file = './wg_iotp_sensors.csv'
    ds = "Asia/Singapore Time"
    y = "Data"
    Y_df = pd.read_csv(file)[[ds, y]].rename(columns={ds: "ds", y: "y"})
    Y_df = Y_df[Y_df.reset_index().index % 180 == 0]

    Y_df["ds"] = pd.to_datetime(Y_df["ds"], errors='coerce')
    Y_df = Y_df.set_index('ds').tz_convert('UTC').tz_localize(None).reset_index()
    Y_df = Y_df.drop_duplicates()
    Y_df["unique_id"] = [123 for _ in range(len(Y_df))]
    Y_train_df = Y_df[Y_df.ds<='2024-08-30'] # 218k train
    Y_train_df = Y_train_df[Y_train_df.ds>'2024-08-21']
    Y_test_df = Y_df[Y_df.ds>'2024-08-30'] # 25k test
    Y_test_df = Y_test_df[Y_test_df.ds<='2024-08-31']
    freq = 'h'

    return Y_train_df, Y_test_df, freq

def do_forecast(Y_train_df, Y_test_df, freq, nf_models, title, ylabel):
    # NeuralForecast - Fit and predict with NBEATS and NHITS models
    horizon = len(Y_test_df)
    models = [
        NBEATS(input_size=2 * horizon, h=horizon, max_steps=50),
        NHITS(input_size=2 * horizon, h=horizon, max_steps=50),
    ]
    nf = NeuralForecast(models=models, freq=freq)
    start1 = time.process_time()
    nf.fit(df=Y_train_df)
    nf_train_time = time.process_time() - start1
    Y_hat_df = nf.predict().reset_index()

    # Plot predictions
    fig, ax = plt.subplots(1, 1, figsize = (16, 7))
    Y_hat_df = Y_test_df.merge(Y_hat_df, how='left', on=['unique_id', 'ds'])
    plot_df = pd.concat([Y_train_df, Y_hat_df]).set_index('ds')

    # NeuralProphet
    model = NeuralProphet(
    )
    start2 = time.process_time()
    model.fit(Y_train_df[['ds','y']])
    np_train_time = time.process_time() - start2
    future = model.make_future_dataframe(df=Y_test_df, periods=12, n_historic_predictions=True)
    forecast = model.predict(future[['ds','y']])
    np_result = forecast.rename(columns={"yhat1": "np_predict"}).set_index("ds")


    # Add to plot
    plot_df = plot_df.merge(np_result, how='left', on=['y', 'ds'])


    # FbProphet
    model = Prophet(
    )
    start3 = time.process_time()
    model.fit(Y_train_df[['ds','y']])
    fb_train_time = time.process_time() - start3
    # future = model.make_future_dataframe(periods=12)
    forecast = model.predict(future)[["ds", "yhat", "yhat_lower", "yhat_upper"]]
    fb_result = forecast.join(Y_train_df[['ds','y']].set_index("ds"), on="ds").set_index(["ds"])
    fb_result = forecast.rename(columns={"yhat": "fb_predict"}).set_index("ds")


    # Add to plot
    plot_df = plot_df.merge(fb_result, how='left', on=['ds'])

    # training time
    print(f"{nf_train_time=} seconds")
    print(f"{np_train_time=} seconds")
    print(f"{fb_train_time=} seconds")

    # Config plot
    # columns = ['y_x'] + nf_models
    columns = ['y'] + nf_models + ['np_predict', 'fb_predict', 'yhat_upper', 'yhat_lower']
    plot_df[columns].plot(ax=ax, linewidth=1)

    ax.set_title(title, fontsize=22)
    ax.set_ylabel(ylabel, fontsize=20)
    ax.set_xlabel('Timestamp [t]', fontsize=20)
    ax.legend(prop={'size': 15})
    ax.grid()

    plt.show()


if __name__ == "__main__":
    source = "iotp_sensors"  # airpassengers, sinwave, iotp_sensors
    nf_models = [
        'NBEATS', 
        'NHITS',
    ]

    if source == "airpassengers":
        Y_train_df, Y_test_df, freq = load_airpassengers()
        do_forecast(
            Y_train_df,
            Y_test_df, 
            freq,
            nf_models,
            title = "AirPassengers Forecast",
            ylabel = "Monthly Passengers",
        )
    elif source == "sinwave":
        Y_train_df, Y_test_df, freq = load_sinwave()
        do_forecast(
            Y_train_df, 
            Y_test_df, 
            freq,
            nf_models,
            title = "Sin Wave Forecast",
            ylabel = "Fake Data",
        )
    else:
        Y_train_df, Y_test_df, freq = load_iotp_sensors()
        do_forecast(
            Y_train_df, 
            Y_test_df, 
            freq,
            nf_models,
            title = "IOTP Sensors",
            ylabel = "Sensor Data",
        )
        