from responses_data import get_random_response
from servant_data import (fetch_roster, build_lookup, build_alias_lookup, find_servant_in_text,
                          find_class_in_text, mentions_classes, class_overview)
from tamamo_voice import describe_servant, describe_class, classes_overview_reply, generic_servant_reply
from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import re
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

nltk.download('stopwords')
nltk.download('wordnet')

app = Flask(__name__)
CORS(app)

model = joblib.load('chatbot_model.pkl')
vectorizer = joblib.load('vectorizer.pkl')

servant_roster = fetch_roster()
servant_lookup = build_lookup(servant_roster)
servant_aliases = build_alias_lookup(servant_lookup)
print(f"Loaded {len(servant_lookup)} servants for name recognition.")

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))


def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", '', text)
    tokens = text.split()
    tokens = [lemmatizer.lemmatize(t) for t in tokens if t not in stop_words]
    return ' '.join(tokens)


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

    matched_servant = find_servant_in_text(text, servant_lookup, servant_aliases)
    if matched_servant and (intent in ('servant_info', 'fallback') or confidence < threshold):
        return describe_servant(matched_servant), 'servant_info', confidence, 'servant'

    class_key = find_class_in_text(text)
    if class_key and (intent in ('servant_info', 'fallback') or confidence < threshold):
        count, examples = class_overview(servant_roster, class_key)
        return describe_class(class_key, count, examples), 'servant_info', confidence, 'servant'

    if confidence < threshold:
        return get_random_response('fallback_unclear'), intent, confidence, 'unclear'

    if intent == 'fallback':
        return get_random_response('fallback_offtopic'), intent, confidence, 'offtopic'

    if intent == 'servant_info':
        if mentions_classes(text):
            return classes_overview_reply(), intent, confidence, 'servant'
        return generic_servant_reply(), intent, confidence, 'servant'

    return get_random_response(intent), intent, confidence, 'answer'

predict_intent("warm up")
find_servant_in_text("warm up", servant_lookup, servant_aliases)


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_msg = data.get('message', '')
    if not user_msg.strip():
        return jsonify({'error': 'Empty message'}), 400

    reply, intent, confidence, kind = get_response(user_msg)
    return jsonify({
        'reply': reply,
        'intent': intent,
        'confidence': round(float(confidence), 2),
        'kind': kind
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
