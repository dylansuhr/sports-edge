# Compliance & Legal Policy

**Last Updated**: 2025-01-XX
**Version**: 1.0

---

## Overview

This document outlines the legal and compliance policies for the **sports-edge** betting research platform. This platform is designed **exclusively for research, analysis, and educational purposes**. It does **not** automate bet placement and operates strictly within legal boundaries.

---

## 1. Human-in-the-Loop Policy

### Explicit Statement
**sports-edge does NOT automate bet placement.**

All betting decisions require explicit human review and manual execution. The platform serves as a **decision support tool** only.

### Workflow

```
1. Data Collection (Automated)
   ↓ The Odds API fetches market data

2. Signal Generation (Automated)
   ↓ Models calculate fair probabilities and identify +EV opportunities

3. **HUMAN REVIEW** (Manual)
   ↓ User reviews signals in dashboard

4. Bet Placement (Manual)
   ↓ User manually places bets via sportsbook app/website

5. Bet Tracking (Manual)
   ↓ User manually records bets in database or CSV

6. Settlement & Analysis (Automated)
   ↓ System processes results and calculates P&L, CLV
```

### Code Enforcement

- **No API integrations** with betting sites (DraftKings, Caesars, FanDuel, etc.)
- **No automated execution** of trades or wagers
- **No credentials** for sportsbook accounts stored or used
- All signals stored in `signals` table with `status='active'` for review
- Dashboard is **read-only** with no write/execute capabilities

### Audit Trail

Every signal generated is logged immutably in the `signals` table with:
- UUID (unique identifier)
- Timestamp (`generated_at`)
- Model version (`model_version`)
- All input parameters (odds, fair probability, edge %, etc.)

This creates a complete audit trail for review and compliance verification.

---

## 2. Terms of Service Compliance

### Data Providers

**The Odds API**
- Usage: ToS-compliant data fetching for odds and results
- Rate limits: Enforced via `rate_limit_seconds` (default: 6 seconds between requests)
- Quota tracking: Monitored via response headers (`x-requests-remaining`)
- Attribution: Not required for non-commercial research use
- Commercial use: Requires separate commercial license from The Odds API

**Restrictions**:
- ❌ No scraping of betting sites directly
- ❌ No circumventing API rate limits
- ❌ No redistribution of raw data to third parties
- ✅ Personal research and analysis permitted
- ✅ Historical data caching in local database

### Sportsbook ToS

**sports-edge does NOT**:
- Access sportsbook accounts programmatically
- Automate bet placement
- Use bots or automated tools for wagering
- Engage in coordinated betting schemes
- Share account credentials

**Users must**:
- Manually place all bets via official sportsbook apps/websites
- Comply with sportsbook terms of service
- Not use the platform for prohibited activities (e.g., bonus abuse, arbitrage if prohibited)

---

## 3. API Key Security

### Environment Variables

All API keys and sensitive credentials are stored in `.env` (never committed to git):

```bash
# The Odds API
THE_ODDS_API_KEY=your_api_key_here

# Database (production)
DATABASE_URL=postgresql://user:pass@host:5432/db

# Database (read-only)
DATABASE_READONLY_URL=postgresql://readonly_user:pass@host:5432/db
```

### Security Best Practices

1. **Never commit `.env`** to version control
   - `.env` is in `.gitignore`
   - Use `.env.template` for documentation

2. **Use read-only database role** for dashboard
   - Separate credentials for read-only access
   - Prevents accidental data modification from dashboard

3. **Rotate API keys** periodically
   - Recommended: every 90 days
   - Immediately upon suspected compromise

4. **Limit API key scope**
   - Only grant necessary permissions
   - Use separate keys for dev/prod if available

5. **Monitor API usage**
   - Track quota via logs
   - Alert on unusual activity

---

## 4. Legal Disclaimers

### Gambling Laws

**Disclaimer**: Sports betting is subject to federal, state, and local laws. Users are solely responsible for ensuring compliance with all applicable laws in their jurisdiction.

**sports-edge**:
- Does not provide legal advice
- Does not facilitate illegal gambling
- Is not liable for user actions or losses

**User Responsibilities**:
- Verify sports betting is legal in your jurisdiction
- Only use legal, licensed sportsbooks
- Comply with age restrictions (21+ in most US states)
- Report gambling winnings for tax purposes

### Educational Use Only

This platform is intended for:
- ✅ Sports betting research and education
- ✅ Statistical modeling and analysis
- ✅ Personal decision support
- ✅ Learning about sports analytics

This platform is NOT intended for:
- ❌ Professional gambling operations
- ❌ Coordinated betting syndicates
- ❌ Circumventing sportsbook limits or bans
- ❌ Commercial betting services

### No Warranty

**sports-edge** is provided "AS IS" without warranties of any kind:
- No guarantee of profitability
- No guarantee of accuracy (models can be wrong)
- No liability for financial losses
- No guarantee of uptime or availability

**Past performance does not guarantee future results.**

### Financial Risk

Sports betting involves substantial financial risk:
- You can lose money
- Models may have errors or biases
- Markets are efficient and edges are small
- Variance can cause extended losing streaks

**Only wager what you can afford to lose.**

---

## 5. Responsible Gambling

### Bankroll Management

- Set a fixed bankroll separate from living expenses
- Never chase losses
- Follow fractional Kelly sizing (¼-Kelly recommended)
- Max stake: 1% of bankroll per bet
- Max daily risk: 5% of bankroll

### Problem Gambling Resources

If you or someone you know has a gambling problem:

- **National Problem Gambling Helpline**: 1-800-522-4700
- **Online Support**: [ncpgambling.org](https://www.ncpgambling.org/)
- **Self-Exclusion Programs**: Available through most sportsbooks

**Warning Signs**:
- Betting more than you can afford to lose
- Chasing losses
- Neglecting work, school, or relationships
- Borrowing money to gamble

**sports-edge encourages responsible gambling practices.**

---

## 6. Data Privacy

### Data Collection

**sports-edge** collects and stores:
- Odds data from The Odds API (public market data)
- Game schedules and results (public data)
- User-entered bet tracking data (optional)
- Signal generation parameters

**sports-edge does NOT collect**:
- Sportsbook account credentials
- Personal financial information
- Payment information
- Personally identifiable information (PII)

### Data Storage

- Database: Postgres (self-hosted or managed service)
- Backups: User-managed (not stored on third-party servers)
- Data retention: Indefinite (for historical analysis)

### Data Sharing

**sports-edge does NOT**:
- Share data with third parties
- Sell data to advertisers
- Provide data to sportsbooks
- Use data for purposes other than research

---

## 7. Age Restrictions

**You must be 21 years or older** (or the legal gambling age in your jurisdiction) to use **sports-edge** for sports betting purposes.

By using this platform, you certify that:
- You meet the minimum age requirement
- Sports betting is legal in your jurisdiction
- You will comply with all applicable laws

---

## 8. Liability Limitations

**sports-edge** and its creators are NOT liable for:
- Financial losses from betting
- Errors in odds data or model predictions
- Downtime or service interruptions
- Violations of sportsbook ToS by users
- Legal consequences of user actions

**By using sports-edge, you accept all risks and responsibilities.**

---

## 9. Code of Conduct

Users agree to:
- Use the platform ethically and legally
- Not engage in fraudulent activity
- Not abuse promotions or bonuses (if prohibited by sportsbooks)
- Not use the platform to harm others
- Respect intellectual property rights

**Prohibited Activities**:
- Automated betting or botting
- Hacking or unauthorized access
- Data theft or scraping
- Commercial resale of signals or data
- Coordinated betting rings or syndicates

---

## 10. Updates to This Policy

This compliance document may be updated periodically. Changes will be noted with:
- Version number increment
- "Last Updated" date change
- Summary of changes in git commit message

**Users are responsible for reviewing updates.**

---

## 11. Contact

For compliance questions or to report violations:

- **GitHub Issues**: [anthropics/sports-edge/issues](https://github.com/yourusername/sports-edge/issues)
- **Email**: (Add if applicable)

---

## Summary Checklist

- ✅ **Human-in-the-loop**: All bets manually placed
- ✅ **ToS Compliance**: Using authorized APIs only
- ✅ **API Security**: Keys in `.env`, never committed
- ✅ **Legal Disclaimers**: Clear risk warnings
- ✅ **Responsible Gambling**: Bankroll limits and resources
- ✅ **Data Privacy**: No PII collection
- ✅ **Age Restrictions**: 21+ enforcement
- ✅ **Liability Limits**: No warranty on results
- ✅ **Code of Conduct**: Ethical use policy

---

**By using sports-edge, you acknowledge that you have read, understood, and agree to comply with this policy.**
