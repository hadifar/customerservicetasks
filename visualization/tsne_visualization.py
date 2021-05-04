import argparse
import random
from itertools import chain
from random import sample

import numpy as np
import torch
from matplotlib import pyplot as plt
from matplotlib.legend_handler import HandlerTuple
from matplotlib.lines import Line2D
from sklearn.manifold import TSNE
from transformers import AutoModel, AutoTokenizer

from utils import get_replies

model = AutoModel.from_pretrained("xlm-roberta-base")
tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")


def sample_tweets(dir_path, company_name, num_sample=30):
    replies = get_replies(dir_path, company_name)
    if num_sample != -1:
        return sample(replies, num_sample)
    return replies


def extract_features(replies):
    all_features = []
    total_example = len(replies)
    for i, line in enumerate(replies):
        input_ids = torch.tensor([tokenizer.encode(line)])
        with torch.no_grad():
            feature = model(input_ids)
        # feature = feature[1].data.numpy().squeeze()
        feature = feature['pooler_output'].data.numpy().squeeze()
        all_features.append(feature)

        if i % 50 == 49:
            print('{}/{}'.format(i, total_example))

    return np.array(all_features)


def plot_tsne(features, labels, n_sample):
    colors = ['#440154', '#481567', '#238A8D', '#1F968B', '#DCE319', '#FDE725']

    symbols = 'P', 'X', 'o', 'p', 'v', '^'

    X = np.array(list(chain(*features)))

    markers = [[symbols[i]] * n_sample for i in labels]
    markers = np.array(list(chain(*markers)))

    tsne = TSNE(n_components=2)
    X_2d = tsne.fit_transform(X)

    fig, ax = plt.subplots()
    ax.tick_params(labelbottom=False)
    ax.tick_params(labelleft=False)

    marker_size = 5

    handles = []
    for i, s in enumerate(symbols):
        ind = np.where(markers == s)[0]
        h, = ax.plot(X_2d[:, 0][ind], X_2d[:, 1][ind],
                     ls='none',
                     c=colors[i],
                     marker=s,
                     markersize=marker_size)
        handles.append(h)

    legend_elements2 = [
        Line2D([0], [0], marker=symbols[i], color='w',
               markerfacecolor=colors[i], markersize=marker_size) for i in range(6)  # 6 companies
    ]

    ax.legend([(legend_elements2[0], legend_elements2[1]),
               (legend_elements2[2], legend_elements2[3]),
               (legend_elements2[4], legend_elements2[5])],
              ['Airline', 'Telecom', 'Public transport'],
              handler_map={tuple: HandlerTuple(ndivide=None)}
              , loc='upper right', title='Sectors', markerscale=1.4)

    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    plt.show()
    plt.draw()

    fig.savefig('fig_tsne.png')


def main(args):
    airlines = ['flyingbrussels', 'flyswiss']
    mobile_operator = ['telenet', 'threeuk']
    public_transport = ['delijn', 'Metrolinx']

    all_companies = airlines + mobile_operator + public_transport

    all_features = []
    all_labels = []
    for i, c in enumerate(all_companies):
        replies = sample_tweets(args.dir_path, c.lower(), num_sample=args.n_samples)
        features = extract_features(replies)
        all_features.append(features)
        all_labels.append(i)

    plot_tsne(all_features, all_labels, args.n_samples)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--dir_path', type=str, default='./corpora-latest',
                        help="directory to save the conversations")
    #
    parser.add_argument('--clean_type', type=str, default='medium', help='level of pre-processing',
                        choices=['medium', 'hard', 'soft', 'none'])

    parser.add_argument('--n_samples', type=int, default=150, help='number of samples tweet per company')

    args = parser.parse_args()
    main(args)
