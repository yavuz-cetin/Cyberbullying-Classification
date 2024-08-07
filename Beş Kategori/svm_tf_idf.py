# -*- coding: utf-8 -*-
"""SVM tf-idf.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1V47Zxq-yUXoFe41a7Fwy6xaJIbf85Dzd
"""

import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC

data = pd.read_csv('data/processed.csv')
data['Tweets'].fillna('', inplace=True)

X = data['Tweets']
y = data['Tag']

sampled_data = data.sample(n=10000, random_state=42)
X_sampled = sampled_data['Tweets']
y_sampled = sampled_data['Tag']

tfidf_vectorizer = TfidfVectorizer()
X_counts_sampled = tfidf_vectorizer.fit_transform(X_sampled)

X_train_sampled, X_test_sampled, y_train_sampled, y_test_sampled = train_test_split(X_counts_sampled, y_sampled, test_size=0.2, random_state=42)

svm_model = SVC()

param_grid = {
    'kernel': ['linear', 'rbf'],
    'C': [0.1, 1, 10, 100],
    'gamma': ['scale', 'auto']
}

grid_search = GridSearchCV(svm_model, param_grid, cv=5, n_jobs=-1, verbose=2)
grid_search.fit(X_train_sampled, y_train_sampled)

best_params = grid_search.best_params_
best_score = grid_search.best_score_

print("Best Parameters:", best_params)
print("Best Cross-Validation Score (from GridSearchCV):", best_score)

tfidf_vectorizer = TfidfVectorizer()
X_counts_full = tfidf_vectorizer.fit_transform(X)
X_train_full, X_test_full, y_train_full, y_test_full = train_test_split(X_counts_full, y, test_size=0.2, random_state=42)

best_svm_model = SVC(kernel=best_params['kernel'], C=best_params['C'], gamma=best_params['gamma'])
best_svm_model.fit(X_train_full, y_train_full)

test_score = best_svm_model.score(X_test_full, y_test_full)
print("Test Score with the best model:", test_score)

cv_scores = cross_val_score(best_svm_model, X_counts_full, y, cv=5)
print("Cross-Validation Scores with the best model:", cv_scores)
print("Average Cross-Validation Score with the best model:", cv_scores.mean())

from sklearn.metrics import classification_report

y_predict = best_svm_model.predict(X_test_full)

category_mapping = {
    0: 'not_cyberbullying',
    1: 'religion',
    2: 'gender',
    3: 'ethnicity',
    4: 'age'
}

print(classification_report(y_test_full.map(category_mapping), [category_mapping[label] for label in y_predict]))

import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay
from sklearn.metrics import confusion_matrix
cm = confusion_matrix(y_test_full, y_predict)
label = ['not', 'religion', 'gender', 'ethnicity', 'age']
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=label)
disp.plot(cmap=plt.cm.Blues)
plt.title('SVM CV Confusion Matrix')
plt.show()