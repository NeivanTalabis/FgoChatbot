import re
import joblib
import pandas as pd
import matplotlib.pyplot as plt
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay

nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

df = pd.read_csv('fgo_dataset.csv')
print(f"Loaded {df.shape[0]} rows")
print(df['intent'].value_counts())
print()

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", '', text)
    tokens = text.split()
    tokens = [lemmatizer.lemmatize(t) for t in tokens if t not in stop_words]
    return ' '.join(tokens)

df['clean_text'] = df['text'].apply(clean_text)

X_train, X_test, y_train, y_test = train_test_split(
    df['clean_text'], df['intent'],
    test_size=0.2, random_state=42, stratify=df['intent']
)
print(f"Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")
print()

vectorizer = TfidfVectorizer()
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

model = LogisticRegression(max_iter=1000)
model.fit(X_train_vec, y_train)

y_pred = model.predict(X_test_vec)
report_text = classification_report(y_test, y_pred)
print(report_text)

cm = confusion_matrix(y_test, y_pred, labels=model.classes_)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=model.classes_)
fig, ax = plt.subplots(figsize=(8, 8))
disp.plot(ax=ax, xticks_rotation=45)
plt.tight_layout()
plt.savefig('confusion_matrix.png')
print("Saved confusion_matrix.png")
print()

from sklearn.pipeline import make_pipeline
from sklearn.model_selection import RepeatedStratifiedKFold, cross_validate

cv_pipe = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000))
cv_res = cross_validate(cv_pipe, df['clean_text'], df['intent'],
                        cv=RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=42),
                        scoring=['accuracy', 'f1_macro'])
cv_acc, cv_f1 = cv_res['test_accuracy'], cv_res['test_f1_macro']
cv_text = (f"5-fold cross-validation, repeated 3 times ({len(cv_acc)} folds):\n"
           f"  accuracy {cv_acc.mean():.3f} +/- {cv_acc.std():.3f}  (range {cv_acc.min():.3f}-{cv_acc.max():.3f})\n"
           f"  macro F1 {cv_f1.mean():.3f} +/- {cv_f1.std():.3f}  (range {cv_f1.min():.3f}-{cv_f1.max():.3f})")
print(cv_text)
print()

cm_df = pd.DataFrame(cm, index=model.classes_, columns=model.classes_)
with open('model_results.txt', 'w', encoding='utf-8') as f:
    f.write(f"Dataset: {len(df)} rows; train {len(X_train)} / test {len(X_test)} "
            f"(stratified 80/20, random_state=42)\n")
    f.write(df['intent'].value_counts().to_string() + "\n\n")
    f.write("Classification report (held-out test split):\n" + report_text + "\n")
    f.write("Confusion matrix (rows = true intent, columns = predicted):\n" + cm_df.to_string() + "\n\n")
    f.write(cv_text + "\n")
print("Saved model_results.txt")
print()

joblib.dump(model, 'chatbot_model.pkl')
joblib.dump(vectorizer, 'vectorizer.pkl')
print("Saved chatbot_model.pkl and vectorizer.pkl")
print()

from responses_data import get_random_response
from tamamo_voice import generic_servant_reply

def predict_intent(text):
    clean = clean_text(text)
    vec = vectorizer.transform([clean])
    probs = model.predict_proba(vec)[0]
    best_idx = probs.argmax()
    confidence = probs[best_idx]
    intent = model.classes_[best_idx]
    return intent, confidence

def get_response(text, threshold=0.20):
    intent, confidence = predict_intent(text)
    if confidence < threshold:
        return get_random_response('fallback_unclear'), intent, confidence
    if intent == 'fallback':
        return get_random_response('fallback_offtopic'), intent, confidence
    if intent == 'servant_info':
        return generic_servant_reply(), intent, confidence
    return get_random_response(intent), intent, confidence

try:
    import app as _live

    def get_response(text):
        reply, intent, confidence, _kind = _live.get_response(text)
        return reply, intent, confidence

    print("(Sample conversations use the live server logic from app.py)")
except Exception as e:
    print(f"(Sample conversations use the simplified logic, without servant lookup: {e})")

test_messages = [
    "hey there", "what's fgo about", "how do the gacha rates work",
    "tell me about gilgamesh", "how do i beat this boss", "is there an event going on",
    "is this game worth playing", "what's a good game like this",
    "what's the weather today", "idk"
]

print("=== Sample conversations ===")
for msg in test_messages:
    reply, intent, conf = get_response(msg)
    print(f"USER: {msg}")
    print(f"  -> intent: {intent} (confidence: {conf:.2f})")
    print(f"  -> BOT: {reply}\n")
