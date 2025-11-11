# Frequently Asked Questions (FAQ)

**Last Updated:** November 11, 2025

---

## General Questions

### What is Socrates?

Socrates is an AI-powered platform that guides teams through systematic requirements gathering using the Socratic method (question-based discovery). It helps create complete, high-quality specifications across seven knowledge domains.

### Who should use Socrates?

Socrates is ideal for:
- **Software teams** building products
- **Enterprises** creating system specifications
- **Startups** defining MVPs
- **Consultants** gathering client requirements
- **Educators** teaching requirements engineering

### What makes Socrates different from other tools?

1. **Systematic approach** - Seven-domain coverage ensures nothing is missed
2. **AI-powered** - Claude AI asks intelligent questions, not templates
3. **Socratic method** - Discovers requirements through dialogue
4. **Cross-domain** - Integrates insights across domains
5. **Collaborative** - Team-based specification development
6. **Metrics-driven** - Maturity and confidence scores

### How much does it cost?

Socrates uses a SaaS subscription model:
- **Starter:** $99/month (5 projects, 3 members)
- **Professional:** $499/month (unlimited, all features)
- **Enterprise:** Custom pricing

Free trial available. See pricing page for details.

---

## Getting Started

### How do I get started?

1. **Sign up** at socrates.app
2. **Create a project** with your project name
3. **Start a session** and choose a domain
4. **Answer questions** from the AI
5. **Review generated specifications**
6. **Export or share** with your team

See [Getting Started Guide](GETTING_STARTED.md) for detailed instructions.

### Do I need technical knowledge?

No! Socrates is designed for anyone. You just need to:
- Understand your project
- Think through answers clearly
- Be honest about unknowns
- Involve relevant stakeholders

### How long does a session take?

**Single domain:** 20-30 minutes
**Multiple domains:** 45-60 minutes
**Quick session:** 15 minutes

No need to rush - take time to think through answers.

### Can I do multiple sessions?

Yes! You can:
- Create multiple sessions for the same project
- Focus on different domains in each session
- Refine and update specifications over time
- Build complete specifications incrementally

---

## Features & Functionality

### What are the seven domains?

1. **Architecture** - System design and structure
2. **Programming** - Implementation and tech stack
3. **Testing** - Quality assurance strategy
4. **Data Engineering** - Data management and analytics
5. **Security** - Security and compliance
6. **Business** - Business context and goals
7. **DevOps** - Operations and deployment

Each domain has 15-20 targeted questions.

### What is a workflow?

A **workflow** executes a defined process:
- Covers multiple domains simultaneously
- Asks questions across domains
- Detects cross-domain conflicts
- Provides integrated analysis
- Generates comprehensive specifications

**Example:** "MVP Definition" workflow covers Architecture, Programming, and Testing to create a runnable product specification.

### Can I create custom domains?

Currently, the seven pre-configured domains cover most needs. Custom domains are planned for future versions (Enterprise tier).

### How does maturity scoring work?

**Maturity score (0-1)** shows how complete your specifications are:
- `0.0-0.3` - Early stage (concept)
- `0.3-0.6` - Moderate (some clarity)
- `0.6-0.8` - Mature (well-defined)
- `0.8-1.0` - Complete (production-ready)

The score increases as you add specifications and complete sessions.

### What is confidence scoring?

**Confidence score (0-1)** on each specification shows how certain you are:
- `0.0-0.3` - Uncertain, needs discussion
- `0.3-0.6` - Provisional, may change
- `0.6-0.8` - Solid, unlikely to change
- `0.8-1.0` - Certain, stable

Low confidence items should be discussed with team.

### How does conflict detection work?

Socrates automatically detects when:
- Two specifications contradict each other
- A specification conflicts with assumptions
- Missing information creates gaps
- Assumptions aren't validated

When conflicts are found, you're notified and guided to resolution.

---

## Collaboration & Sharing

### Can I work with a team?

Yes! Socrates is designed for teams:
- Invite team members to projects
- Assign roles (owner, editor, viewer)
- Collaborate on sessions
- Discuss specifications in comments
- Track who changed what

### What are the roles?

| Role | Permissions |
|------|------------|
| **Owner** | Full control, add members, delete project |
| **Editor** | Edit specs, start sessions, add members |
| **Viewer** | Read-only access |

### How do I invite team members?

1. Go to Project → Team
2. Click "Add Member"
3. Enter their email
4. Select role
5. Send invitation

They'll receive an email and can accept the invitation.

### Can I share projects with external people?

Yes! You can:
- Share project link (view-only)
- Invite specific users
- Set expiration dates on shares
- Revoke access anytime

### How do I export specifications?

```
Project → Export
Select format: Markdown, PDF, JSON, or CSV
Choose content to include:
  - All specifications
  - Analysis
  - Team info
  - History
Download file
```

**Best formats for:**
- **Documentation:** Markdown or PDF
- **Analysis:** JSON or CSV
- **Sharing:** PDF or Markdown
- **Tools Integration:** JSON

---

## Technical Questions

### What is the Socratic method?

The Socratic method is a teaching technique using questions to:
1. Guide discovery
2. Uncover hidden assumptions
3. Test understanding
4. Build clarity gradually
5. Encourage critical thinking

Socrates applies this to requirements gathering.

### How does AI analyze my answers?

Socrates uses Claude AI to:
- Understand your answers in context
- Generate follow-up questions
- Identify assumptions
- Detect potential conflicts
- Synthesize specifications
- Provide recommendations

The AI never stores personal data beyond your project.

### Can I access via API?

Yes! Socrates provides:
- Full REST API (40+ endpoints)
- JWT authentication
- Complete API documentation
- Python, JavaScript, TypeScript SDKs
- Webhook support

See [API Reference](../developer/API_REFERENCE.md).

### Is the data encrypted?

Yes:
- Transmission: HTTPS/TLS encryption
- Storage: Database-level encryption
- Passwords: Bcrypt hashing
- API Keys: Encrypted storage

Enterprise tier offers additional security features.

### What about data privacy?

Socrates is SOC 2 compliant (planned):
- End-to-end encryption available
- GDPR compliant
- Data residency options (Enterprise)
- Regular security audits
- No third-party data sharing

See [Privacy Policy](https://socrates.app/privacy).

---

## Troubleshooting

### I can't log in

**Solutions:**
- Check email/password spelling
- Verify email is confirmed
- Reset password if forgotten
- Clear browser cookies
- Try incognito mode

### Session won't start

**Solutions:**
- Ensure project is created first
- Check network connection
- Refresh the page
- Try different domain
- Check browser console for errors

### Questions seem off-topic

**This is normal:**
- Questions are context-aware
- They build on previous answers
- Some jump between topics to check understanding
- Each question has a purpose

If question is truly unclear, let us know!

### I can't find my project

**Solutions:**
- Check you're logged in as correct user
- Use search functionality
- Check Team section for shared projects
- Sort by date (most recent first)
- Check if archived

### Export didn't work

**Solutions:**
- Check format selection
- Ensure you have specifications
- Try different format (PDF, JSON, CSV)
- Check file size (large exports take time)
- Check download folder

### Team member can't access

**Solutions:**
- Verify email invitation was sent
- Check they confirmed invitation
- Verify they're logged in
- Check their user role
- Try re-inviting if needed

### Specifications disappeared

**Don't worry!**
- Check filters aren't hiding them
- Check session they belong to
- Check status filter (draft/approved/implemented)
- Use search function
- All changes are version-tracked

### AI gives strange answers

**This can happen:**
- Provide more context in answers
- Use clearer, more specific language
- Correct the AI if it misunderstands
- Session context matters - earlier answers affect later questions
- Report issues so we can improve

---

## Account & Billing

### How do I upgrade my plan?

1. Go to Account → Billing
2. Click "Upgrade Plan"
3. Select new plan
4. Enter payment info
5. Confirm upgrade

Changes take effect immediately.

### Can I cancel anytime?

Yes! Cancel anytime:
1. Account → Billing
2. Click "Cancel Subscription"
3. Confirm cancellation

No cancellation fees. You'll have access until renewal date.

### What payment methods do you accept?

- Credit/debit cards (Visa, Mastercard, Amex)
- Bank transfers (Enterprise)
- Purchase orders (Enterprise)

All payments processed securely.

### Can I download my data?

Yes! You can:
- Export all projects
- Export all specifications
- Download full JSON backup
- Request data transfer

See Account → Data Management.

---

## Best Practices

### Tips for Better Specifications

1. **Start with Architecture** - Understand design first
2. **Be specific** - Vague answers lead to vague specs
3. **Involve stakeholders** - Get diverse perspectives
4. **Review regularly** - Check specs after each session
5. **Address conflicts** - Don't ignore contradictions
6. **Document assumptions** - Track why decisions were made
7. **Update maturity** - Reflect true completeness

### Tips for Great Sessions

- **Take your time** - 30 minutes beats 10 rushed minutes
- **Have context** - Understand project before starting
- **Get team input** - Include all perspectives
- **Ask clarifications** - If question is unclear
- **Be honest** - About unknowns and assumptions
- **Review results** - Check generated specs immediately

### Tips for Team Collaboration

- **Clear ownership** - Someone drives requirements
- **Regular meetings** - Sync on specs regularly
- **Document decisions** - Record rationale
- **Address conflicts early** - Don't let disagreements fester
- **Use comments** - Discuss in context
- **Share widely** - Make everyone aware

---

## Advanced Topics

### Can I integrate with other tools?

**Coming soon:**
- GitHub (sync to repositories)
- Jira (create issues from specs)
- Confluence (publish specifications)
- Slack (notifications)

API integrations available now.

### Can I use different LLMs?

Currently Socrates uses Claude (Anthropic). Multi-LLM support is planned for future versions.

### Is there an on-premise option?

Enterprise tier supports on-premise deployment. Contact sales for details.

### Can I white-label Socrates?

Yes! Enterprise customers can white-label:
- Custom branding
- Custom domain
- Custom themes
- Embedded experience

Contact sales@socrates.app.

---

## Getting Help

### Where can I find more help?

- **Full Documentation:** [View Docs](../INDEX.md)
- **User Guide:** [User Guide](USER_GUIDE.md)
- **Getting Started:** [Quick Start](GETTING_STARTED.md)
- **Tutorials:** [Step-by-Step Tutorials](TUTORIALS.md)

### How do I report a bug?

1. Email: support@socrates.app
2. GitHub: Create issue on repository
3. In-app: Use "Report Issue" button

Include:
- What happened
- What you expected
- Steps to reproduce
- Screenshots

### How do I request a feature?

1. Email: feedback@socrates.app
2. GitHub: Create feature request
3. In-app: Use "Suggest Feature" button

We read all feedback and prioritize based on demand.

### Can I schedule a demo?

Yes! Book a demo at: https://socrates.app/demo

Or email: demo@socrates.app

---

## Still Have Questions?

- **Email:** support@socrates.app
- **Live Chat:** Available on socrates.app
- **Community:** Discussion forum (coming soon)
- **Docs:** [Complete Documentation](../INDEX.md)

We're here to help! 🚀

---

**[← Back to User Documentation](USER_GUIDE.md)**
**[← Back to Documentation Index](../INDEX.md)**
