# Questionable
![Group Image](logo.png)

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-API-4285F4?logo=google&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-DB-3ECF8E?logo=supabase&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automation-2088FF?logo=githubactions&logoColor=white)


---
## Game Purpose
Questionable is a daily chaos generator for your Telegram group. Every day, a fresh question drops, and the poll options? The names of your own crew.
It’s messy, fun, and a little bit ruthless. Vote on who fits the question best and watch the drama unfold. Built for laughs, banter, and keeping your group on its toes :).

---

## Overview

**Questionable** consists of two main components:

1. **Question Generator** : A Python script that generates a new daily question using the **Gemini API**.  
2. **Telegram Bot** : A bot that retrieves the latest question from a **Supabase database** and publishes it as a poll in a Telegram group.

Every day, via **GitHub Actions**, the question generator runs automatically, stores the question in Supabase. Finally the Telegram bot is triggered, retrieves the question and publish it.

---

## Pipeline
![Group Image](pipeline_bot5.png)

---

## Prerequisites
  
- Telegram Bot Token (from [BotFather](https://t.me/botfather))  
- Supabase project with database access
- Gemini API key
- Group Chat Id of your own Telegram group chat

---

## Supabase DB

A single table named questions with 4 columns:
- id
- question
- created_at
- context

---

## Build your own Questionable
Questionable was born because our group chat wanted to have fun, but without spending a single penny.
You can do the same! All the required services (GitHub, Supabase, Gemini, and Telegram Bot) offer free tiers that fully cover this use case, so you can build your own Questionable!

These are the steps you have to follow:

1. Create a repository on GitHub (you can clone this repository or add each component by hand).
2. You can edit the contexts list or the model prompt in the `update_question.py` file to change language or style of the question as you like (currently the style is "simple" but you can make it "punk" or even more "family friendly").
3. Create a Telegram group chat and make anyone in the group admin.
4. Get a Google AI API key.
5. Create a Supabase Project and build the questions table as specified, you can use the `create_questions_table.txt` file content and run it in the Supabase SQL editor.
6. Create a Telegram Bot, add it to your group chat and make it admin.
7. Store the required API keys and token (look at update_question.py and bot.py) in the GitHub Secrets key section. (`Settings->Security->Secrets and variables->Actions->New repository secret`)
8. Now enjoy the chaos with your friends :).

---

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

---

## Setup

1. **Clone the repository**

```bash
git clone https://github.com/foughtmoss/questionable.git
cd questionable
