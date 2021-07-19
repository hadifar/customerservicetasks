# A million tweets are worth a few points

This repository contains the code for the presented paper in NAACL 2021:

```
@inproceedings{8708982,
  abstract     = {{In online domain-specific customer service applications, many companies struggle to deploy advanced NLP models successfully, due to the limited availability of and noise in their datasets. While prior research demonstrated the potential of migrating large open-domain pretrained models for domain-specific tasks, the appropriate (pre)training strategies have not yet been rigorously evaluated in such social media customer service settings, especially under multilingual conditions. We address this gap by collecting a multilingual social media corpus containing customer service conversations (865k tweets), comparing various pipelines of pretraining and finetuning approaches, applying them on 5 different end tasks. We show that pretraining a generic multilingual transformer model on our in-domain dataset, before finetuning on specific end tasks, consistently boosts performance, especially in non-English settings.}},
  author       = {{Hadifar, Amir and Labat, Sofie and Hoste, Veronique and Develder, Chris and Demeester, Thomas}},
  booktitle    = {{Proceedings of the 2021 Conference of the North American Chapter of the Association for Computational Linguistics : Human Language Technologies}},
  location     = {{Online}},
  pages        = {{220--225}},
  publisher    = {{Association for Computational Linguistics (ACL)}},
  title        = {{A million tweets are worth a few points : tuning transformers for customer service tasks}},
  url          = {{http://dx.doi.org/10.18653/v1/2021.naacl-main.21}},
  year         = {{2021}},
}
```


[A Million Tweets Are Worth a Few Points: Tuning Transformers for Customer Service Tasks](https://arxiv.org/pdf/2104.07944.pdf)



## Install dependencies

`pip install -r requirement.txt`

## Data preparation

`data_preparation` folder contains scripts for crawling and cleaning Twitter conversations for more than 100 companies in different sectors which they have enough interactions with their clients. 

## Data visualization

`visualization` folder contains a script for TSNE visualization in the paper

![alt text](https://github.com/hadifar/customerservicetasks/blob/master/visualization/fig_tsne.png)


## Evaluation 
