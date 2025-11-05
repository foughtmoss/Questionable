# Questionable

![Group Image](groupimgprofile.png)

**Questionable** consiste di due componenti principali:

1. **Question Generator**  
2. **Telegram Bot**

Ogni giorno, utilizzando **GitHub Actions**, uno script Python genera una nuova domanda tramite la **Gemini API**. La domanda viene poi salvata in un **database Supabase**. Infine, il **Telegram bot** recupera la nuova domanda e la pubblica come sondaggio nel gruppo.

