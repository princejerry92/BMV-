import matplotlib
from flask import Flask,flash, render_template, request, jsonify
matplotlib.use('Agg')  # Use Agg backend for non-interactive plotting

import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
import psutil
import random
import io
import base64
from datetime import datetime

app = Flask(__name__, template_folder='template')


def get_cpu_metrics():
    cpu_usage = [psutil.cpu_percent(interval=1) for _ in range(10)]
    return cpu_usage

def get_network_speed():
    download_speed = random.uniform(50, 150)
    upload_speed = random.uniform(10, 50)
    return download_speed, upload_speed

def create_violin_plot(cpu_metrics):
    plt.figure(figsize=(10, 6))
    sns.violinplot(data=cpu_metrics)
    plt.title("CPU Usage Distribution")
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    img_bytes = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return img_bytes

def create_gauge_chart(value, title, max_value):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title},
        gauge={'axis': {'range': [None, max_value]}},
    ))
    # Increase the width and height to make the gauge bigger
    fig.update_layout(
        width=500,
        height=500,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    buf = io.BytesIO()
    fig.write_image(buf, format="png", engine="kaleido")
    buf.seek(0)
    img_bytes = base64.b64encode(buf.read()).decode('utf-8')
    return img_bytes

if __name__ == '__main__':
        app.run(debug=True)
