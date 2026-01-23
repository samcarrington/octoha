# Octoha - Home Assistant Octopus Energy Integration PRD

## Product Requirements Document (PRD)

### 0. Revision History

| Date       | Author          | Change Description                                         |
| ---------- | --------------- | ---------------------------------------------------------- |
| 2026-01-18 | Developer Agent | Initial draft - Octoha HA integration for smart meter data |
| 2026-01-18 | Tech Lead       | Minor additions and answered questions                     |

### 1. Overview

- **Problem Statement:** Current SMETS integration via the 'Bright' app provides inaccurate energy usage information and is completely broken for gas readings. This makes it impossible to monitor real-time consumption, understand flexible tariff costs, or create meaningful home automations based on energy usage patterns. Users on Octopus Energy's flexible tariffs (Agile, Tracker, Go) need accurate, timely data to optimise their energy usage and reduce costs.

- **Value Proposition:** Octoha provides a reliable, open-source Home Assistant integration that pulls data directly from the Octopus Energy API, delivering accurate gas and electricity usage visualisation, historical consumption data, and automation-ready entities. By following HA's official integration patterns, it offers a maintainable, community-friendly solution that enables users to make informed energy decisions and automate their homes based on real consumption and tariff data.

### 2. Goals & Objectives

**Goals:**

- Provide accurate, reliable smart meter data within Home Assistant, replacing broken Bright/SMETS integration
- Enable HA users to visualise live and historical gas and electricity consumption
- Expose energy data as HA entities for use in automations, scripts, and dashboards
- Deliver an open-source integration following HA official patterns for community adoption

**Objectives:**

- Gas daily readings match Smart Meter IHD (In-Home Display) visualisation exactly
- Electricity usage data accurate within 1 hour of actual consumption
- All core entities available and functional within 30 minutes of initial configuration
- Integration installable via HACS with <5 minute setup time
- 100% compatibility with current Home Assistant release

### 3. Stakeholders

| Name/Group               | Role/Responsibility                  | Contact/Notes                                     |
| ------------------------ | ------------------------------------ | ------------------------------------------------- |
| Primary Developer        | Product Owner, Developer, Maintainer | Personal use + open-source maintainer             |
| Octopus Energy Customers | Primary End Users                    | HA users on Octopus tariffs seeking accurate data |
| Home Assistant Community | Secondary Users & Contributors       | Potential contributors via GitHub                 |
| HACS Community           | Distribution Channel                 | For community discoverability and installation    |

### 4. Specifications & Use Cases

**Primary Use Cases:**

1. **Live Energy Monitoring**: User views current electricity and gas consumption on their HA dashboard in real-time
   - _Acceptance Criteria_: Dashboard displays current usage with visual indicators; updates reflect meter readings within accuracy thresholds

2. **Historical Usage Review**: User reviews previous days' energy consumption to understand usage patterns
   - _Acceptance Criteria_: Summary and/or graph data available for previous days; data accessible via HA's energy dashboard or custom cards

3. **Tariff-Aware Automations**: User creates automations that trigger based on energy consumption or tariff rates
   - _Acceptance Criteria_: Entities expose consumption values and tariff data; triggers available with customisable thresholds

4. **Cost Tracking**: User understands their energy costs based on actual usage and current tariff rates
   - _Acceptance Criteria_: Cost calculation entities available; supports Agile, Tracker, Go, and Flexible tariffs

5. **Initial Setup**: User configures the integration with their Octopus API key via HA settings UI
   - _Acceptance Criteria_: Config flow in HA UI; API key validation; clear error messages for invalid credentials

**Secondary Use Cases:**

6. **Natural Language Queries** (Nice to Have): User asks questions about their energy usage via HA conversation integration
   - _Acceptance Criteria_: Integration exposes data in a format compatible with HA Assist or similar NLP interfaces

### 5. Functional Requirements

**Must Have (P0):**

| ID    | Requirement                                                               | Priority |
| ----- | ------------------------------------------------------------------------- | -------- |
| FR-01 | API key-based authentication with Octopus Energy API                      | Must     |
| FR-02 | HA Settings/Config Flow UI for entering and validating API key            | Must     |
| FR-03 | Live electricity consumption entity (kWh)                                 | Must     |
| FR-04 | Live gas consumption entity (kWh or m³)                                   | Must     |
| FR-05 | Daily electricity usage summary entity                                    | Must     |
| FR-06 | Daily gas usage summary entity                                            | Must     |
| FR-07 | Historical electricity usage (previous days, subject to API availability) | Must     |
| FR-08 | Historical gas usage (previous days, subject to API availability)         | Must     |
| FR-09 | Entities compatible with HA Energy Dashboard                              | Must     |
| FR-10 | Automation triggers with customisable thresholds                          | Must     |
| FR-11 | Follow HA official custom integration patterns                            | Must     |
| FR-12 | Current tariff rate entity (electricity)                                  | Must     |
| FR-13 | Error handling with clear user-facing messages                            | Must     |

**Should Have (P1):**

| ID    | Requirement                                                         | Priority |
| ----- | ------------------------------------------------------------------- | -------- |
| FR-14 | Current tariff rate entity (gas)                                    | Should   |
| FR-15 | Cost calculation entities (daily/weekly/monthly)                    | Should   |
| FR-16 | Support for multiple meter points (MPAN/MPRN)                       | Should   |
| FR-17 | Tariff schedule visualisation data (e.g., Agile rates for next 24h) | Should   |
| FR-18 | HACS installation support                                           | Should   |
| FR-19 | Sensor attributes with metadata (tariff name, meter serial, etc.)   | Should   |
| FR-20 | Configurable polling interval                                       | Should   |

**Could Have (P2):**

| ID    | Requirement                                                 | Priority |
| ----- | ----------------------------------------------------------- | -------- |
| FR-21 | Natural language query support via HA Assist/Conversation   | Could    |
| FR-22 | Push notifications for rate changes (Agile low-rate alerts) | Could    |
| FR-23 | Intelligent Octopus Go dispatch schedule integration        | Could    |
| FR-24 | Saving Sessions integration                                 | Could    |
| FR-25 | Carbon intensity data integration                           | Could    |
| FR-26 | Export functionality (CSV/JSON)                             | Could    |

### 6. Out of Scope

- Direct SMETS/DCC meter communication (uses Octopus API only)
- Support for non-Octopus energy providers
- Solar/battery/export meter integration (initial release)
- Backwards compatibility with older HA versions
- Mobile app (HA companion app provides this)
- Account management (bill payment, tariff switching)
- Integration with other smart home platforms (Google Home, Alexa directly)
- Real-time sub-second power monitoring (API limitations)

### 7. Non-Functional Requirements

**Performance:**

- Dashboard entities update within 60 seconds of new API data availability
- Initial data load completes within 30 seconds of configuration
- Integration adds <50MB memory footprint to HA instance
- API polling respects rate limits (no more than 1 request/minute per endpoint)

**Security:**

- API keys stored securely using HA's credential storage
- No API keys logged or exposed in debug output
- HTTPS-only communication with Octopus API
- Credentials never transmitted to third parties

**Reliability:**

- Graceful handling of API outages with cached last-known values
- Automatic retry with exponential backoff on transient failures
- Clear entity state indication when data is stale or unavailable
- Integration recovery without restart after network restoration

**Maintainability:**

- Code follows HA integration development guidelines
- Comprehensive logging at DEBUG level for troubleshooting
- Unit test coverage for core API client functionality
- Documentation for installation, configuration, and troubleshooting

**Compatibility:**

- Compatible with current Home Assistant release (2024.1+)
- Python 3.11+ (HA requirement)
- No external dependencies beyond HA core and standard libraries where possible

### 8. Success Metrics

#### Technical Success Metrics

1. **Metric:** Gas Reading Accuracy
   - **Baseline:** Bright app shows incorrect/missing gas data (current state: broken)
   - **Target:** Daily gas readings match Smart Meter IHD exactly (100% accuracy)
   - **Timeframe:** From first stable release
   - **Datasource:** Manual comparison with IHD display; user validation
   - **Owner:** Primary Developer
   - **Guardrails:** No data loss during API polling; graceful degradation if API unavailable

2. **Metric:** Electricity Data Freshness
   - **Baseline:** No reliable HA integration (current state: N/A)
   - **Target:** Electricity usage accurate within 1 hour of actual consumption
   - **Timeframe:** From first stable release
   - **Datasource:** HA entity last_updated timestamp vs. Octopus API data timestamp
   - **Owner:** Primary Developer
   - **Guardrails:** Data latency clearly indicated in entity attributes; no false readings

3. **Metric:** Entity Availability
   - **Baseline:** N/A (new integration)
   - **Target:** All core entities available within 30 minutes of configuration
   - **Timeframe:** From initial setup
   - **Datasource:** HA entity registry; integration setup logs
   - **Owner:** Primary Developer
   - **Guardrails:** Setup fails fast with clear error if API credentials invalid

4. **Metric:** Integration Stability
   - **Baseline:** N/A (new integration)
   - **Target:** Zero unhandled exceptions in 7-day continuous operation
   - **Timeframe:** During beta testing period
   - **Datasource:** HA logs; GitHub issue tracker
   - **Owner:** Primary Developer
   - **Guardrails:** Memory usage stable; no HA restart required for recovery

#### User Experience Metrics

5. **Metric:** Setup Time
   - **Baseline:** N/A (new integration)
   - **Target:** <5 minutes from HACS install to working dashboard
   - **Timeframe:** From first HACS release
   - **Datasource:** User feedback; setup flow timing
   - **Owner:** Primary Developer
   - **Guardrails:** Config flow validates all inputs; helpful error messages

### 9. Constraints & Assumptions

**Technical Constraints:**

- Octopus Energy API rate limits and data availability windows
- Smart meter data typically available with 30-minute to 24-hour delay from Octopus
- GraphQL API may change without notice (unofficial API)
- Single developer resource for initial implementation

**Business Constraints:**

- Open-source project with no commercial backing
- Dependent on Octopus Energy maintaining API access
- No formal SLA for support or updates

**Assumptions:**

- User has valid Octopus Energy account with API access enabled
- User's smart meter is enrolled and sending data to Octopus
- Octopus API continues to provide GraphQL access (as used by open-octopus reference)
- Home Assistant instance is accessible for integration installation
- User has MPAN (electricity) and/or MPRN (gas) available for configuration
- API patterns from open-octopus repository remain valid and can be adapted

### 10. Timeline & Milestones

#### Phase 1: Foundation & API Integration (Week 1-2)

- Fork/reference open-octopus for API patterns
- Implement core Octopus API client (Python, async)
- API key authentication and account validation
- Basic electricity consumption data retrieval
- Unit tests for API client

#### Phase 2: HA Integration Structure (Week 3-4)

- HA custom integration scaffolding (config flow, manifest)
- Config flow UI for API key entry and validation
- Core sensor entities (electricity current, daily)
- Integration with HA Energy Dashboard

#### Phase 3: Gas & Historical Data (Week 5-6)

- Gas consumption entities (current, daily)
- Historical data retrieval and entity attributes
- Tariff rate entities (electricity, gas)
- Entity attributes (metadata, timestamps)

#### Phase 4: Automations & Polish (Week 7-8)

- Automation triggers with customisable thresholds
- Error handling and recovery improvements
- Documentation (README, setup guide)
- HACS manifest and repository structure

#### Phase 5: Testing & Release (Week 9-10)

- Beta testing on personal HA instance
- Validation against Smart Meter IHD
- Bug fixes and refinements
- Initial public release (GitHub + HACS)

**Critical Dependencies:**

- Octopus API documentation/patterns (from open-octopus reference)
- Valid Octopus account with working smart meter data
- Home Assistant development environment

### 11. Risks & Mitigations

| Risk                                        | Probability | Impact | Mitigation Strategy                                                                                           |
| ------------------------------------------- | ----------- | ------ | ------------------------------------------------------------------------------------------------------------- |
| Octopus API changes or access revoked       | Medium      | High   | Monitor open-octopus repo for changes; implement version detection; abstract API layer for easier updates     |
| Smart meter data delay exceeds expectations | Medium      | Medium | Document data freshness limitations clearly; show last_updated prominently; set appropriate user expectations |
| GraphQL API rate limiting                   | Low         | Medium | Implement respectful polling; exponential backoff; cache responses; configurable intervals                    |
| Gas data unavailable or format differs      | Medium      | High   | Validate gas endpoints early in development; fallback to electricity-only if needed for MVP                   |
| HA integration patterns change              | Low         | Medium | Follow official HA documentation; use HA development tools for validation; target current HA version only     |
| Single developer bandwidth constraints      | Medium      | Medium | Prioritise P0 requirements; scope MVP tightly; defer P2 features to future releases                           |

### 12. Open Questions

#### Technical Questions

- What is the exact data refresh frequency from Octopus API for live consumption?
- Does the GraphQL API provide real-time power (W) or only cumulative consumption (kWh)?

Full GraphQL documentation is [available online](https://docs.octopus.energy/graphql/reference/)

- What historical data range is available via API (days, weeks, months)?
- Are there different API endpoints for different tariff types?

#### Integration Questions

- Should we support HA's native energy dashboard statistics, or custom entities only?

Support native energy dashboard wherever possible - if the API offers additional capability we can brainstorm a solution.

- What entity naming convention is preferred (e.g., `sensor.octoha_electricity_daily`)?

This convention looks good

- Should the integration support reconfiguration without removal/reinstall?

Yes, in the event of a changed API Key I would like to be able to reconfigure the dashboard without nuking the install.

#### Scope Questions

- If natural language support is pursued, should it use HA Assist, or a custom approach?

Open Octopus appears to integrate with Claude for natural language support https://github.com/abracadabra50/open-octopus/blob/main/src/open_octopus/agent.py consider that as baseline for now.

- Should Intelligent Go dispatch schedules be P1 or P2 priority?

I am an intelligent Go customer so P1

- Is there demand for multi-property support (users with multiple Octopus accounts)?

No demand for now but put it on the roadmap

### 13. References & Related Documents

#### External References

- [open-octopus Repository](https://github.com/abracadabra50/open-octopus) - Reference implementation for Octopus API patterns
- [Octopus Energy Developer API](https://developer.octopus.energy/docs/api/) - Official REST API documentation
- [Home Assistant Developer Docs - Integration](https://developers.home-assistant.io/docs/creating_integration_manifest) - HA integration patterns
- [Home Assistant Developer Docs - Config Flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler) - Config flow implementation
- [HACS Documentation](https://hacs.xyz/docs/publish/start) - Publishing to HACS

#### Project Documentation

- [ADR-001: Octoha Technical Architecture](../ADRs/adr-001-octoha-architecture.md) - Architecture decisions and rationale
- [Entity Relationship Diagram & Data Models](../designs/octoha-erd-data-models.md) - Data models and entity mappings
- [Component Architecture](../designs/octoha-component-architecture.md) - HA integration structure and implementation details
- Installation & Configuration Guide (To Be Created)

---

_This PRD is ready for product review. It will be updated as discovery progresses and technical spikes resolve open questions._
