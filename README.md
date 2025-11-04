# Questionable

**Questionable** consists of two main components:

1. **Question Generator**  
2. **Telegram Bot**

Every day, using **GitHub Actions**, a Python script generates a new question via the **Gemini API**. The question is then stored in a **Supabase database**. Finally, the **Telegram bot** retrieves the new question and publishes it as a poll in the group.
