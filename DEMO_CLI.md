# Socrates CLI Demo

This document shows example CLI sessions to demonstrate functionality.

## Demo 1: Basic Workflow (Socratic Mode)

```bash
$ python Socrates.py

╔═══════════════════════════════════════════════════════════════╗
║                    SOCRATES CLI v1.0                          ║
║          AI-Powered Specification Gathering                   ║
╚═══════════════════════════════════════════════════════════════╝

Type /help for available commands or just start chatting!

Please /login or /register to get started

socrates 🤔 > /register

Register New Account

Email: alice@example.com
Full name: Alice Developer
Password: ********
Confirm password: ********

✓ Account created successfully!
User ID: 550e8400-e29b-41d4-a716-446655440000

Please login with /login

socrates 🤔 > /login

Login

Email: alice@example.com
Password: ********

✓ Logged in successfully as alice@example.com

socrates 🤔 > /project create

Create New Project

Project name: E-commerce API
Description (optional): Backend API for online store

✓ Project created: 7c9e6679-7425-40de-944b-e6f3a3a8e3a0
Selected project: E-commerce API

E-commerce API 🤔 > /session start

✓ Session started: b3f4a3c2-1234-5678-9012-a1b2c3d4e5f6

Ready to begin Socratic questioning!
Just type your thoughts and press Enter to continue the conversation.

Socrates:
╔════════════════════════════════════════════════════════════════════╗
║ Let's begin by understanding what you're building. Could you       ║
║ describe the main purpose of your e-commerce API?                  ║
╚════════════════════════════════════════════════════════════════════╝

E-commerce API session 🤔 > I want to build a backend for an online store that sells handmade crafts

Socrates:
╔════════════════════════════════════════════════════════════════════╗
║ That's a great start. Handmade crafts are unique products.        ║
║ What are the most important features your sellers need to         ║
║ manage their inventory effectively?                                ║
╚════════════════════════════════════════════════════════════════════╝

✓ Extracted 1 specification(s):
  • Product type: Handmade crafts with unique characteristics

E-commerce API session 🤔 > They need to add products with multiple photos, descriptions, and track stock levels

✓ Extracted 3 specification(s):
  • Product feature: Multiple photo uploads per product
  • Product feature: Rich text descriptions
  • Inventory feature: Real-time stock level tracking

Socrates:
╔════════════════════════════════════════════════════════════════════╗
║ Good. Now thinking about the shopping experience - how should     ║
║ customers be able to browse and search for these unique items?    ║
╚════════════════════════════════════════════════════════════════════╝

E-commerce API session 🤔 > By category, material type, price range, and seller

✓ Extracted 4 specification(s):
  • Search filter: Category-based filtering
  • Search filter: Material type filtering
  • Search filter: Price range filtering
  • Search filter: Seller-based filtering

E-commerce API session 🤔 > /history

Conversation History

[2025-11-07 21:45] Socrates:
╔════════════════════════════════════════════════════════════════════╗
║ Let's begin by understanding what you're building...               ║
╚════════════════════════════════════════════════════════════════════╝

[2025-11-07 21:46] You:
╔════════════════════════════════════════════════════════════════════╗
║ I want to build a backend for an online store that sells          ║
║ handmade crafts                                                    ║
╚════════════════════════════════════════════════════════════════════╝

[... full history shown ...]

E-commerce API session 🤔 > /session end

End current session? [y/n]: y

✓ Session ended
Specifications extracted: 8

E-commerce API 🤔 > /exit

Goodbye! Keep building great things! 🚀
```

## Demo 2: Direct Chat Mode

```bash
$ python Socrates.py

Welcome back, alice@example.com!

socrates 🤔 > /project select 7c9e6679

✓ Selected project: E-commerce API

E-commerce API 🤔 > /mode direct

✓ Switched to direct mode 💬
Direct mode: Direct conversation with AI assistant

E-commerce API 💬 > What's the best way to handle product images in an API?

Socrates:
╔════════════════════════════════════════════════════════════════════╗
║ There are several approaches for handling product images in APIs: ║
║                                                                    ║
║ 1. Direct Upload to API Server                                    ║
║    - Upload via multipart/form-data                               ║
║    - Store on server filesystem or database                        ║
║    - Pros: Simple, full control                                    ║
║    - Cons: Scalability issues, server load                        ║
║                                                                    ║
║ 2. Cloud Storage (S3, Google Cloud Storage)                       ║
║    - Upload directly to cloud storage                              ║
║    - API stores only the URL reference                            ║
║    - Pros: Scalable, CDN-ready, cost-effective                    ║
║    - Cons: Additional service dependency                           ║
║                                                                    ║
║ 3. Pre-signed URLs                                                 ║
║    - Client gets temporary upload URL from API                     ║
║    - Uploads directly to storage                                   ║
║    - API notified of completion                                    ║
║    - Pros: No API bandwidth, secure, scalable                     ║
║    - Cons: More complex flow                                       ║
║                                                                    ║
║ Recommendation for e-commerce:                                     ║
║ Use approach #3 (pre-signed URLs) with S3-compatible storage.     ║
║ This gives you the best performance and scalability.              ║
╚════════════════════════════════════════════════════════════════════╝

E-commerce API 💬 > Can you help me spec out the image upload endpoint?

Socrates:
╔════════════════════════════════════════════════════════════════════╗
║ Here's a specification for the image upload endpoint:             ║
║                                                                    ║
║ POST /api/v1/products/{product_id}/images/upload-url               ║
║                                                                    ║
║ Request:                                                           ║
║ {                                                                  ║
║   "filename": "craft-photo-1.jpg",                                ║
║   "content_type": "image/jpeg",                                    ║
║   "file_size_bytes": 524288                                        ║
║ }                                                                  ║
║                                                                    ║
║ Response:                                                          ║
║ {                                                                  ║
║   "upload_url": "https://s3.../presigned-url",                    ║
║   "image_id": "uuid",                                             ║
║   "expires_at": "2025-11-07T22:00:00Z"                           ║
║ }                                                                  ║
║                                                                    ║
║ After upload, confirm with:                                        ║
║ POST /api/v1/products/{product_id}/images/{image_id}/confirm      ║
╚════════════════════════════════════════════════════════════════════╝

✓ Extracted 2 specification(s):
  • API endpoint: POST /api/v1/products/{product_id}/images/upload-url
  • API endpoint: POST /api/v1/products/{product_id}/images/{image_id}/confirm

E-commerce API 💬 > Perfect! Thanks

E-commerce API 💬 > /mode socratic

✓ Switched to socratic mode 🤔
Socratic mode: Thoughtful questioning to extract specifications

E-commerce API 🤔 > /exit
```

## Demo 3: Project Management

```bash
$ python Socrates.py

Welcome back, alice@example.com!

socrates 🤔 > /projects

┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ ID        ┃ Name           ┃ Description         ┃ Phase ┃ Maturity ┃ Created    ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━┩
│ → 7c9e667 │ E-commerce API │ Backend API for...  │ 1     │ 45.2%    │ 2025-11-05 │
│   a1b2c3d │ Task Manager   │ Team task tracking  │ 2     │ 78.5%    │ 2025-11-03 │
│   xyz789a │ Chat Bot       │ Customer support... │ 1     │ 12.0%    │ 2025-11-01 │
└───────────┴────────────────┴─────────────────────┴───────┴──────────┴────────────┘

socrates 🤔 > /project select a1b2c3d

✓ Selected project: Task Manager

Task Manager 🤔 > /sessions

┏━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ ID        ┃ Status   ┃ Questions ┃ Specs ┃ Created        ┃
┡━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━┩
│   b3f4a3c │ complete │        15 │    42 │ 2025-11-03 ... │
│   c5d6e7f │ active   │         8 │    23 │ 2025-11-04 ... │
│   g9h0i1j │ complete │        12 │    35 │ 2025-11-02 ... │
└───────────┴──────────┴───────────┴───────┴────────────────┘

Task Manager 🤔 > /project info

Project Information

Name: Task Manager
ID: a1b2c3d4-5678-90ef-ghij-klmnopqrstuv
Description: Team task tracking and collaboration system
Phase: 2
Maturity Score: 78.5%
Created: 2025-11-03T10:30:00Z
Updated: 2025-11-04T15:45:00Z

Task Manager 🤔 > /whoami

Logged in as: alice@example.com
Current project: Task Manager (a1b2c3d4-5678-90ef-ghij-klmnopqrstuv)
```

## Demo 4: Session Management

```bash
$ python Socrates.py

Welcome back, alice@example.com!

socrates 🤔 > /projects

[List shown]

socrates 🤔 > /project select 7c9e667

✓ Selected project: E-commerce API

E-commerce API 🤔 > /session start

✓ Session started: new-session-id

[Socratic conversation begins...]

E-commerce API session 🤔 > /sessions

┏━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ ID        ┃ Status   ┃ Questions ┃ Specs ┃ Created        ┃
┡━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ → new-ses │ active   │         3 │     8 │ 2025-11-07 ... │
│   old-ses │ complete │        15 │    42 │ 2025-11-05 ... │
└───────────┴──────────┴───────────┴───────┴────────────────┘

E-commerce API session 🤔 > /history

[Full conversation history shown]

E-commerce API session 🤔 > /session end

End current session? [y/n]: y

✓ Session ended
Specifications extracted: 8
```

## Demo 5: Error Handling

```bash
$ python Socrates.py

socrates 🤔 > /project create

You need to login first. Use /login or /register

socrates 🤔 > /login

Email: user@example.com
Password: ********

✗ Login failed: Invalid credentials

socrates 🤔 > /register

[...successful registration...]

socrates 🤔 > /session start

No project selected. Use /project select <id> or /project create

socrates 🤔 > /project create

[...create project...]

E-commerce API 🤔 > I want to build an API

Start a session with /session start to begin Socratic chat

E-commerce API 🤔 > /mode direct

✓ Switched to direct mode 💬

E-commerce API 💬 > I want to build an API

[Direct chat works without session!]
```

## Demo 6: Help System

```bash
$ python Socrates.py

socrates 🤔 > /help

╔═══════════════════════════════════════════════════════════════╗
║                    Socrates CLI Help                          ║
╚═══════════════════════════════════════════════════════════════╝

Available Commands:

Authentication:
  /register              Register new account
  /login                 Login to existing account
  /logout                Logout from current session
  /whoami                Show current user information

[... full help shown ...]

Chat Modes:

Socratic Mode (default):
The AI uses Socratic questioning to help you think deeply about your
requirements. It asks thoughtful questions to extract specifications.
Requires an active session (/session start).

Direct Mode:
Chat directly with the AI assistant without structured questioning.
Great for quick questions, clarifications, or general discussion.
No session required.

Examples:
  /project create
  /session start
  I want to build a REST API for managing tasks
```

## Demo 7: Debug Mode

```bash
$ python Socrates.py --debug

[Banner shown]

socrates 🤔 > /debug

Debug mode: ON

socrates 🤔 > /login

[If error occurs, full stack trace is shown]

socrates 🤔 > /debug

Debug mode: OFF
```

## Notes

These demos show:
1. ✅ User registration and authentication
2. ✅ Project creation and management
3. ✅ Socratic questioning mode
4. ✅ Direct chat mode
5. ✅ Mode switching
6. ✅ Session management
7. ✅ History viewing
8. ✅ Error handling
9. ✅ Help system
10. ✅ Beautiful formatting with Rich

The CLI provides a complete interface for the Socrates system with an intuitive, Claude Code-inspired UX.
