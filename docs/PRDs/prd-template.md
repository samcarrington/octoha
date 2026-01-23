# David Carrington Portfolio Site - PRD

## Product Requirements Document (PRD)

### 0. Revision History

| Date       | Author | Change Description |
| ---------- | ------ | ------------------ |
| 2025-10-23 | Sam Carrington   | Initial draft - portfolio reshape for retirement showcase      |

### 1. Overview

- **Problem Statement:** David Carrington's current WordPress portfolio site is structured for active job seeking and consulting work, but he is now retired and wants to showcase his substantial charity sector contributions as a professional legacy. The current IA and content organization doesn't effectively highlight his past achievements or provide an appropriate digital presence for his retirement years.

- **Value Proposition:** Transform the portfolio from a job-seeking tool into a compelling professional legacy showcase that honors David's charity sector career, makes his work easily discoverable for colleagues and researchers, and provides a modern, performant platform for sharing his expertise and connecting with the charity community.

### 2. Goals & Objectives

**Goals:**

- Create a professional legacy showcase that honors David's charity sector career achievements
- Establish a modern, accessible digital presence appropriate for his retirement years
- Provide an authoritative resource for colleagues, researchers, and charity sector professionals to discover and learn from his work
- Migrate from WordPress to a modern, maintainable JAMstack architecture

**Objectives:**

- Achieve 90+ Lighthouse Performance Score on all pages (vs current unknown baseline)
- Restructure content to prioritize past work showcase over active career seeking by December 2025
- Migrate 100% of valuable existing content with improved organization and discoverability
- Reduce site maintenance overhead through modern architecture and automated deployments
- Implement content structure that supports future additions of retrospective content and professional reflections

### 3. Stakeholders

| Name/Group             | Role/Responsibility | Contact/Notes       |
| ---------------------- | ------------------- | ------------------- |
| David Carrington | Site Owner & Content Authority | Primary stakeholder, subject of portfolio, content validation |
| Sam Carrington | Product Owner & Developer | Technical delivery, project management, development |
| Charity Sector Colleagues | Primary Audience | End users who will discover and reference David's work |
| Professional Network | Secondary Audience | Colleagues and contacts from David's career |
| Family & Friends | Tertiary Audience | Personal connections interested in his professional journey |

### 4. Specifications & Use Cases

**Primary Use Cases:**

1. **Professional Legacy Discovery**: Charity sector professionals and researchers can easily discover and explore David's contributions, projects, and expertise areas
   - *Acceptance Criteria*: Clear navigation to key projects, searchable content, categorized work by charity focus area

2. **Career Journey Showcase**: Visitors can understand David's professional journey and expertise evolution in the charity sector
   - *Acceptance Criteria*: Chronological timeline view available, clear career progression narrative, key achievements highlighted

3. **Knowledge Sharing**: David can share insights, reflections, and expertise gained from his charity sector career
   - *Acceptance Criteria*: Blog/insights section with categories, easy content management via Contentful, SEO-optimized content

4. **Professional Networking**: Colleagues and contacts can learn about David's work and maintain professional connections
   - *Acceptance Criteria*: Contact information available, social/professional links, about section with current status

5. **Content Management**: David can easily add retrospective content, project details, and professional reflections
   - *Acceptance Criteria*: Contentful CMS with intuitive interface, <2 minute publishing workflow, preview functionality

### 5. Functional Requirements

**Must Have (P0):**

- Homepage that clearly positions David as retired charity sector professional with legacy showcase focus
- Portfolio/Projects section organized by charity focus areas (e.g., homelessness, mental health, community development)
- Professional biography with career timeline and key achievements
- Contact page with appropriate contact methods for retirement context
- Responsive design optimized for all devices
- SEO optimization for professional discovery
- Content migration from existing WordPress site
- Modern performance standards (90+ Lighthouse score)

**Should Have (P1):**

- Blog/Insights section for sharing professional reflections and sector expertise
- Search functionality across projects and content
- Project case studies with outcomes and impact metrics
- Professional recommendations/testimonials section
- Resource sharing (reports, presentations, useful links for charity sector)
- Social media integration (LinkedIn, professional networks)

**Could Have (P2):**

- Interactive career timeline visualization
- Downloadable CV/resume in modern format
- Newsletter signup for occasional updates
- Photo gallery of key career moments and events
- Speaking engagements and conference presentations archive
- Mentoring/advisory availability section

### 6. Out of Scope

- Job seeking functionality (career opportunities, availability for hire messaging)
- Client onboarding or business development features
- E-commerce or payment processing capabilities
- User authentication or member-only content areas
- Real-time collaboration or community features
- Multi-language localization (English only for initial release)
- Integration with charity management systems or databases
- Active consulting or service offering promotion

### 7. Non-Functional Requirements

**Performance:**

- Lighthouse Performance Score ≥90 on all pages
- First Contentful Paint <1.5s
- Largest Contentful Paint <2.5s
- Cumulative Layout Shift <0.1
- Page load time <3s on 3G connection

**Security:**

- HTTPS enforcement across all pages
- Content Security Policy implementation
- Regular security dependency updates
- Secure form handling with CSRF protection

**Usability & Accessibility:**

- WCAG 2.1 AA compliance for accessibility
- Responsive design supporting mobile, tablet, desktop
- Intuitive navigation suitable for all age groups
- Clear typography and sufficient color contrast

**Scalability & Maintenance:**

- JAMstack architecture for optimal performance and low maintenance
- Automated deployments and CI/CD pipeline
- Content management workflow requiring <2 minutes from draft to published
- Minimal hosting costs appropriate for personal site

**SEO & Discoverability:**

- Semantic HTML structure
- Optimized meta tags and structured data
- XML sitemap generation
- Social media sharing optimization

### 8. Success Metrics

**Technical Success Metrics:**

- Lighthouse Performance Score: Target ≥90 (measured monthly)
- Page load times: Target <3s for all pages (measured via Core Web Vitals)
- Uptime: Target 99.9% availability (measured via monitoring)
- Content publishing efficiency: Target <2 minutes from draft to live

**Content & User Engagement:**

- Organic search traffic maintenance: Within 5% of pre-migration levels after 60 days
- Page views on portfolio/projects section: Baseline measurement + growth tracking
- Contact form submissions: Maintain current levels, track professional inquiries
- Time on site for key pages (bio, projects): Target >2 minutes average

**Business/Personal Outcomes:**

- Professional network engagement: Track referrals and mentions from colleagues
- Content freshness: Target minimum 1 new insight/blog post per quarter
- Legacy documentation completeness: 100% of significant projects documented within 6 months
- Maintenance efficiency: <2 hours monthly time investment in site updates

### 9. Constraints & Assumptions

**Technical Constraints:**

- Budget appropriate for personal/retirement site (minimal ongoing costs)
- Single developer resource (Sam Carrington) for implementation
- Content migration dependent on WordPress export capabilities
- Modern browser support only (no legacy browser requirements)

**Content & Business Constraints:**

- Content creation bandwidth limited (David is retired, not actively producing new work)
- Professional tone and presentation standards must be maintained
- Privacy considerations for sharing details of charity sector work
- Some historical content may not be recoverable or appropriate for public display

**Assumptions:**

- David will be available for content review and validation throughout project
- Current WordPress site contains recoverable and valuable content for migration
- Charity sector colleagues and network will be primary audience post-launch
- Contentful free tier will be sufficient for content volume (or budget allows paid tier)
- Domain ownership and DNS control are available for migration
- Professional network values digital presence for staying connected with David's work

### 10. Timeline & Milestones

#### **Phase 1: Discovery & Planning (Oct 23 - Nov 6, 2025)**

- WordPress content export and analysis
- Information architecture redesign for retirement/legacy focus
- Contentful content modeling based on charity sector organization

#### **Phase 2: Foundation & Setup (Nov 6 - Nov 27, 2025)**

- Nuxt 3 + Nuxt UI application foundation
- Contentful space configuration
- CI/CD pipeline and hosting setup

#### **Phase 3: Content Migration & Development (Nov 27 - Dec 18, 2025)**

- Content migration scripts and execution
- Core page development (homepage, portfolio, bio, contact)
- SEO optimization and performance tuning

#### **Phase 4: Testing & Launch (Dec 18 - Dec 30, 2025)**

- Cross-browser testing and accessibility validation
- Content review and final approvals with David
- Production deployment and DNS cutover

#### **Critical Dependencies:**

- David's availability for content review (ongoing)
- WordPress export success (blocking for Phase 2)
- Content validation and IA approval (blocking for Phase 3)

### 11. Risks & Mitigations

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|-------------------|
| Content migration data loss | Medium | High | Multiple export formats, validation scripts, staged migration with rollback capability |
| SEO ranking loss during migration | Medium | High | Comprehensive redirect mapping, URL structure preservation, gradual transition |
| Content organization doesn't suit legacy/retirement narrative | Medium | Medium | Early IA validation with David, iterative content structure refinement |
| Limited ongoing content creation bandwidth | High | Low | Focus on evergreen content, retrospective documentation, minimal maintenance design |
| Professional network doesn't engage with new site | Low | Medium | Soft launch with personal outreach, gradual promotion through existing channels |
| Technical complexity exceeds single developer capacity | Low | High | Use proven technologies, phased approach, focus on essential features first |

### 12. Open Questions

#### **Content Strategy:**

- What specific charity sector focus areas should be highlighted most prominently?
- How much detail is appropriate to share about specific charity partnerships and outcomes?
- Should the site include a "lessons learned" or professional reflections section?

#### **Information Architecture:**

- Should content be organized chronologically (career timeline) or thematically (focus areas)?
- How should we balance professional accomplishments with personal retirement status?
- What level of contact availability should be indicated (availability for mentoring, advisory roles, etc.)?

#### **Technical Decisions:**

- Which Contentful pricing tier will be required based on final content volume?
- Should we implement any analytics beyond basic Google Analytics for this audience?
- What level of search functionality is needed (basic site search vs. advanced filtering)?

#### **Future Considerations:**

- Will David want to add new content types (e.g., retrospective articles, industry commentary)?
- Should the site architecture support potential collaboration or guest content from colleagues?

### 13. References & Related Documents

#### **Project Planning:**

- [WordPress to Nuxt Migration Plan](../../plans/wordpress-to-nuxt-migration-plan.md) - Detailed technical implementation plan
- [Project TODO List](../../plans/TODO.md) - Task tracking and progress management

#### **Technical Documentation:**

- [Nuxt 3 Documentation](https://nuxt.com/docs) - Framework reference
- [Nuxt UI Documentation](https://ui.nuxt.com/) - Component library reference
- [Contentful Documentation](https://www.contentful.com/developers/docs/) - CMS integration guidance

#### **Design & Architecture:**

- Technical Architecture ADR (to be created)
- Content Model Documentation (to be created)
- Information Architecture Wireframes (to be created)

#### **Current State Analysis:**

- WordPress Site Audit (to be conducted as part of T-001)
- Content Inventory and Taxonomy (to be created as part of T-002)
- Performance Baseline Assessment (to be conducted as part of T-003)

#### External References

---

*This PRD will be updated as discovery progresses and requirements are refined through stakeholder feedback.*
