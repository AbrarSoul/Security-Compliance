import os
import sys

import requests

API_KEY = os.environ.get("GPTLAB_API_KEY", "")
API_BASE = os.environ.get(
    "GPTLAB_API_BASE",
    "https://gptlab.rd.tuni.fi/GPT-Lab/resources/GPU-farmi-004/v1",
)


def _headers():
    if not API_KEY:
        raise RuntimeError(
            "GPTLAB_API_KEY is not set. Export it in your shell or add it to backend/.env"
        )
    return {"Authorization": f"Bearer {API_KEY}"}


def fetch_models():
    response = requests.get(f"{API_BASE}/models", headers=_headers(), timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"{response.status_code} - {response.text}")
    return [m.get("id", "?") for m in response.json().get("data", [])]


def list_models():
    try:
        models = fetch_models()
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return
    print(f"Available models: {len(models)}\n")
    for i, name in enumerate(models, 1):
        print(f"  {i}. {name}")


def chat(model, messages, max_tokens=1024, timeout=300):
    response = requests.post(
        f"{API_BASE}/chat/completions",
        headers={**_headers(), "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        },
        timeout=timeout,
    )
    if response.status_code != 200:
        raise RuntimeError(f"{response.status_code} - {response.text}")
    return response.json()["choices"][0]["message"]["content"]


def pick_model(models):
    print(f"\nAvailable models: {len(models)}")
    for i, name in enumerate(models, 1):
        print(f"  {i}. {name}")

    while True:
        choice = input("\nPick a model (number or name): ").strip()
        if not choice:
            continue
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(models):
                return models[index - 1]
            print(f"Enter a number between 1 and {len(models)}.")
            continue
        if choice in models:
            return choice
        matches = [m for m in models if choice.lower() in m.lower()]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            print("Multiple matches:")
            for m in matches:
                print(f"  - {m}")
            continue
        print("Model not found. Try again.")


def interactive_chat():
    print("GPT-Lab chat (GPU-farmi-004)\n")
    try:
        models = fetch_models()
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return

    model = pick_model(models)
    history = []
    print(f"\nChatting with: {model}")
    print("Commands: /quit  /model  /clear  /list\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not user_input:
            continue
        if user_input == "/quit":
            print("Bye.")
            break
        if user_input == "/clear":
            history.clear()
            print("Conversation cleared.")
            continue
        if user_input == "/list":
            list_models()
            continue
        if user_input == "/model":
            model = pick_model(models)
            history.clear()
            print(f"\nSwitched to: {model}\n")
            continue

        history.append({"role": "user", "content": user_input})
        print("Assistant: ", end="", flush=True)
        try:
            reply = chat(model, history)
        except RuntimeError as exc:
            print(f"\nError: {exc}")
            history.pop()
            continue
        print(reply)
        history.append({"role": "assistant", "content": reply})
        print()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_models()
    else:
        interactive_chat()
