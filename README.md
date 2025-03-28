# Wedding Taskmaster Challenge: AI Chatbot

This repo contains the code I used to host an AI chatbot for a taskmaster style challenge at my wedding weekend.

The guests were looking for a password in order to progress with a task. The first hint to the password was a cryptic crossword style clue. If they didn't obtain the password that way, they had to use this chatbot instead. The chatbot impersonated me (I gave it some facts about me in the system prompt). It was told that the user was trying to obtain the password, that it would not part with it easily, but that it would tell the user the password if it really liked them. This made for some fun conversations! 

I used the 3 billion parameter Llama 3.2 model, which is small enough that it can run on an ordinary device (so no expensive 3rd party API calls required), but still good enough that it seemed to work really well for this game! I signed up to the Google cloud free trial and used a Google cloud VM to run the server during my wedding weekend, so it cost nothing to set this up. You can't get access to GPUs on the free trial, but the 3B parameter model is so small that it runs ok on a CPU! The only problem is that it can then sometimes take around 30 seconds to generate a response.

The main difficulty in setting this up was that the long response time required everything to work asynchronously, especially as I planned to have lots of people usng this at the same time. The flow is:

- All conversations are stored in a big table in a local sqlite database (local to the docker container, so no persistence).
- When a user sends a request to the flask server (server.py), they are just returned a view of that table, containing their current conversation.
- New messages from the user are added to the sqlite database with a 'response pending' flag.
- A separate process (chat_generator.py) checks the database every 10 seconds for pending messages, and begins generating responses to them one by one, adding the AI generated messages to the table.
- The front end is silently polling the server every 15 seconds, to refresh the conversation and fetch any new messages.
- Cookies are used to track the user's session, so they can resume their conversation later if they don't have time to complete it in one go, or even if they don't have time to wait for the next response (the 'waiting' message informs them it is safe to do this).

The original plan was to have multiple agents that the user could choose from (e.g. one impersonating me and one impersonating my wife) so everything is set up to support that as well.