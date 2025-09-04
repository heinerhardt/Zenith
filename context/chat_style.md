
- HTML
	- Main Structure for all pages

         <!DOCTYPE html>
         <html lang="en">
         <head>
             <meta charset="UTF-8">
             <meta name="viewport" content="width=device-width, initial-scale=1.0">
             <title>Chatbot</title>
             <link rel="stylesheet" href="style.css">
         </head>
         <body>
             <div class="chatbot-container">
                 <div class="chat-header">
                     <h2>Chatbot</h2>
                 </div>
                 <div class="chat-messages" id="chat-messages">
                     </div>
                 <form class="chat-input-form" id="chat-input-form">
                     <input type="text" id="user-input" placeholder="Type your message...">
                     <button type="submit" id="send-btn">Send</button>
                 </form>
             </div>
             <script src="script.js"></script>
         </body>
         </html>

	- LOGIN FORM
	
         <!DOCTYPE html>
         <html lang="en">
         <head>
             <meta charset="UTF-8">
             <meta name="viewport" content="width=device-width, initial-scale=1.0">
             <title>Login - Zenith AI</title>
             <link rel="stylesheet" href="style.css">
         </head>
         <body>
             <div class="login-container">
                 <div class="login-card">
                     <div class="logo">
                         <img src="zenith-ai-logo.svg" alt="Zenith AI Logo">
                     </div>
                     <h1>Intelligent Document Chat System</h1>
                     <form action="#" method="post">
                         <div class="form-group">
                             <label for="username">Username</label>
                             <input type="text" id="username" name="username" required>
                         </div>
                         <div class="form-group">
                             <label for="password">Password</label>
                             <input type="password" id="password" name="password" required>
                         </div>
                         <div class="form-options">
                             <div class="remember-me">
                                 <input type="checkbox" id="remember-me">
                                 <label for="remember-me">Remember Me</label>
                             </div>
                             <a href="#" class="forgot-password">Forgot Password?</a>
                         </div>
                         <button type="submit" class="login-button">Login</button>
                     </form>
                 </div>
             </div>
         </body>
         </html>

- CSS: The Styling

	- Body Style for all pages

        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            /* Blue gradient background */
            background: linear-gradient(to bottom right, #4a90e2, #1f4287);
            color: #333;
        }
        
        .chatbot-container {
            width: 400px;
            height: 600px;
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-header {
            background-color: #1f4287;
            color: white;
            padding: 15px;
            text-align: center;
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
        }
        
        .chat-messages {
            flex-grow: 1;
            padding: 15px;
            overflow-y: auto;
        }
        
        .message {
            display: flex;
            margin-bottom: 10px;
        }
        
        .user-message {
            justify-content: flex-end;
        }
        
        .bot-message {
            justify-content: flex-start;
        }
        
        .user-message .message-bubble {
            background-color: #007bff;
            color: white;
            border-radius: 15px 15px 0 15px;
        }
        
        .bot-message .message-bubble {
            background-color: #f1f1f1;
            color: #333;
            border-radius: 15px 15px 15px 0;
        }
        
        .message-bubble {
            padding: 10px 15px;
            max-width: 75%;
            word-wrap: break-word;
        }
        
        .chat-input-form {
            display: flex;
            padding: 10px;
            background-color: #f1f1f1;
            border-top: 1px solid #ccc;
        }
        
        #user-input {
            flex-grow: 1;
            border: 1px solid #ccc;
            border-radius: 20px;
            padding: 10px 15px;
            outline: none;
        }
        
        #send-btn {
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 20px;
            padding: 10px 20px;
            margin-left: 10px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        #send-btn:hover {
            background-color: #0056b3;
        }


- JavaScript: 

	- For Chat Interactivity

       document.addEventListener("DOMContentLoaded", () => {
           const chatForm = document.getElementById("chat-input-form");
           const userInput = document.getElementById("user-input");
           const chatMessages = document.getElementById("chat-messages");
       
           chatForm.addEventListener("submit", (e) => {
               e.preventDefault();
               const userText = userInput.value.trim();
               if (userText !== "") {
                   addMessage("user", userText);
                   userInput.value = "";
                   simulateBotResponse(userText);
               }
           });
       
           function addMessage(role, text) {
               const messageDiv = document.createElement("div");
               messageDiv.classList.add("message", `${role}-message`);
       
               const bubbleDiv = document.createElement("div");
               bubbleDiv.classList.add("message-bubble");
               bubbleDiv.textContent = text;
       
               messageDiv.appendChild(bubbleDiv);
               chatMessages.appendChild(messageDiv);
       
               // Auto-scroll to the bottom
               chatMessages.scrollTop = chatMessages.scrollHeight;
           }
       
           function simulateBotResponse(userText) {
               // In a real app, this is where you'd send the userText to a back-end API.
               setTimeout(() => {
                   const botResponse = "This is a simulated response. Thanks for your message!";
                   addMessage("bot", botResponse);
               }, 1000);
           }
       });
	
       