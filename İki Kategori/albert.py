# -*- coding: utf-8 -*-
"""ALBERT.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/13YC0ySV7XYnEXgY4yDvmRWici7_TvcFV
"""

#!pip install transformers[torch]
#!pip install accelerate -U
import numpy as np
import pandas as pd
import torch, os
from transformers import pipeline, AlbertForSequenceClassification, AlbertTokenizerFast
from torch.utils.data import Dataset
from torch import cuda

df = pd.read_csv("data/processed_2.csv")
df = df.dropna(subset=['Tweets'])

from imblearn.over_sampling import RandomOverSampler

tweets = np.array(df['Tweets']).reshape(-1, 1)
tags = np.array(df['Tag']).reshape(-1, 1)

ros = RandomOverSampler()

resampled_tweets, resampled_tags = ros.fit_resample(tweets, tags)

resampled_data = list(zip(resampled_tweets.flatten(), resampled_tags.flatten()))

df = pd.DataFrame(resampled_data, columns=['Tweets', 'Tag'])

tokenizer = AlbertTokenizerFast.from_pretrained("albert-base-v2", max_length=512)

import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

label2id = {'not cyberbullying': 0,'cyberbullying': 1}
id2label = {0:'not cyberbullying',1:'cyberbullying'}
model = AlbertForSequenceClassification.from_pretrained("albert-base-v2",num_labels = 2,id2label=id2label,label2id=label2id)
model.to(device)

SIZE = len(df)

split1 = SIZE // 2
split2 = (3 * SIZE) // 4

train_texts = df.Tweets.iloc[:split1].tolist()
val_texts = df.Tweets.iloc[split1:split2].tolist()
test_texts = df.Tweets.iloc[split2:].tolist()

train_labels = df.Tag.iloc[:split1].tolist()
val_labels = df.Tag.iloc[split1:split2].tolist()
test_labels = df.Tag.iloc[split2:].tolist()

len(train_texts)

encodings = {
    'train': tokenizer(train_texts, truncation=True, padding=True),
    'val': tokenizer(val_texts, truncation=True, padding=True),
    'test': tokenizer(test_texts, truncation=True, padding=True)
}

train_encodings = encodings['train']
val_encodings = encodings['val']
test_encodings = encodings['test']

class DataLoader(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

train_dataloader = DataLoader(train_encodings,train_labels)
val_dataloader = DataLoader(val_encodings,val_labels)
test_dataset = DataLoader(test_encodings,test_labels)

from transformers import TrainingArguments, Trainer

from sklearn.metrics import accuracy_score, precision_recall_fscore_support

def compute_metrics(pred):
    true_labels = pred.label_ids
    predicted_labels = pred.predictions.argmax(axis=-1)

    precision, recall, f1_score, _ = precision_recall_fscore_support(
        true_labels, predicted_labels, average='macro'
    )

    accuracy = accuracy_score(true_labels, predicted_labels)

    return {
        'Accuracy': accuracy,
        'F1 Score': f1_score,
        'Precision': precision,
        'Recall': recall
    }

training_args = TrainingArguments(
    output_dir='./CyberALBERT_Model',
    do_train=True,
    do_eval=True,
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    warmup_steps=100,
    weight_decay=0.01,
    logging_strategy='steps',
    logging_dir='./logs/multi_class',
    logging_steps=50,
    evaluation_strategy='steps',
    eval_steps=50,
    save_strategy='steps',
    fp16=True,
    load_best_model_at_end=True
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataloader,
    eval_dataset=val_dataloader,
    compute_metrics=compute_metrics
)

trainer.train()

def predict(text):
  inputs = tokenizer(text,padding=True,truncation=True,max_length=512,return_tensors="pt").to("cuda")
  outputs = model(**inputs)
  probs = outputs[0].softmax(1)
  pred_label_idx = probs.argmax()
  pred_label=model.config.id2label[pred_label_idx.item()]
  return probs,pred_label_idx,pred_label

from sklearn.metrics import classification_report

predicted_labels = []
true_labels = []

for text, true_label in zip(test_texts, test_labels):
    probs, pred_label_idx, pred_label = predict(text)

    predicted_labels.append(pred_label_idx.cpu().item())
    true_labels.append(true_label)

report = classification_report(true_labels, predicted_labels)
print(report)

from sklearn.metrics import  confusion_matrix
from sklearn.metrics import ConfusionMatrixDisplay
import matplotlib.pyplot as plt
cm = confusion_matrix(true_labels, predicted_labels)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['not cyberbullying', 'cyberbullying'])
disp.plot(cmap=plt.cm.Blues)
plt.title('Albert\nConfusion Matrix')
plt.show()