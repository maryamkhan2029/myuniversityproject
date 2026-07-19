import pickle

# load trained model
model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

def predict_intent(text):
    print("INPUT:", text)

    text_vec = vectorizer.transform([text])
    pred = model.predict(text_vec)[0]

    print("PREDICTED INTENT:", pred)

    return pred