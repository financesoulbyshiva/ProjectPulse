# ProjectPulse — UI/UX Specification

**Document Code:** UIUX-PP-V1.0  
**Target Release:** Internship MVP v1.0  
**Design Philosophy:** Clean, Functional, Information-Dense, Human-Centric Data Visualization  
**Theme & Aesthetics:** Modern Slate/Indigo Palette with Semantic Status Accents  
**Status:** Approved  

---

## 1. Global Design System & Navigation Architecture

### 1.1 Color Palette & Semantic Tokens
- **Backgrounds:** Primary Surface `#F8FAFC` (Slate-50), Card/Modal `#FFFFFF` (White), Sidebar `#0F172A` (Slate-900).
- **Primary Brand:** `#4F46E5` (Indigo-600), Hover `#4338CA` (Indigo-700).
- **Risk Semantic Colors:**
  - **Low Risk / Safe:** `#10B981` (Emerald-500) | Badge `#ECFDF5`
  - **Medium Risk / Warning:** `#F59E0B` (Amber-500) | Badge `#FFFBEB`
  - **High Risk / Danger:** `#EF4444` (Rose-500) | Badge `#FEF2F2`
- **Typography:** Inter or system sans-serif font stack.

### 1.2 Layout Structure
- **Persistent Left Sidebar (Desktop $\ge 1024\text{px}$):**
  - Brand Logo & Tagline (*Track. Analyze. Predict. Deliver.*)
  - Navigation Links: Dashboard, Projects, Tasks, Team Analytics, AI Insights
  - Current User Profile snippet & Logout button
- **Mobile/Tablet Top Bar ($< 1024\text{px}$):**
  - Hamburger menu toggling a slide-out drawer navigation.
- **Main Viewport Area:**
  - Breadcrumb header with action buttons (e.g., "+ New Project", "Assess Risk")
  - Scrollable content canvas with max-width $1440\text{px}$ container.

---

## 2. Screen Specifications

### 2.1 Screen 1: Login Screen (`/login`)
- **Purpose:** Secure authentication for Project Managers and Team Members.
- **Layout:** Centered card on a subtle gradient background (`Slate-100` to `Slate-200`).
- **Components:**
  - ProjectPulse logo and tagline.
  - Email text input field.
  - Password input with show/hide toggle.
  - "Sign In" primary button.
  - Demo quick-fill credentials button (for internship presentation & evaluator convenience).
- **Interactions:**
  - Client-side validation for valid email syntax and non-empty password.
  - Submitting authenticates with backend and stores JWT in session/local storage.
- **States:**
  - *Loading:* Spinner on sign-in button, form fields disabled.
  - *Error:* Red alert banner: *"Invalid email or password."*

---

### 2.2 Screen 2: Executive Dashboard (`/dashboard`)
- **Purpose:** High-level executive overview of portfolio health, active projects, and system-wide risk alerts.
- **Layout:** Grid structure with top KPI metric cards, middle split view (Project Health breakdown + Risk Radar), and bottom Recent Activity/Risk list.
- **Components & Data Shown:**
  1. **Top Metric Cards:**
     - Active Projects Count (e.g., `4 Active`).
     - Overall Completion Rate (e.g., `64.2%`).
     - Hours Variance (e.g., `-60 hrs under budget`).
     - Projects At Risk (e.g., `1 Project in Medium/High Risk`).
  2. **Risk Distribution Card:** Visual bar/donut displaying counts of projects in Low, Medium, and High risk.
  3. **Active Projects Table:** Displays Title, Deadline countdown, Progress bar, and Risk Badge.
- **Interactions:**
  - Clicking any project row navigates to that Project's Details screen.
  - Clicking "+ New Project" opens the Project Creation Modal.
- **States:**
  - *Loading:* Skeleton placeholder cards.
  - *Empty:* Illustration with *"No projects created yet. Start by creating your first project."*

---

### 2.3 Screen 3: Projects Screen (`/projects`)
- **Purpose:** Manage the full portfolio of projects with filtering, status tracking, and creation.
- **Layout:** Header with search bar and filter controls, followed by a responsive grid of project cards (3 columns on desktop, 1 on mobile).
- **Components & Data Shown:**
  - **Header Controls:** Search input by title, Status dropdown filter (`All`, `Planning`, `In Progress`, `Completed`), and "+ Create Project" button.
  - **Project Card Elements:**
    - Project Title & Status badge.
    - Start date and Deadline countdown (`X days remaining`).
    - Budget bar: Allocated vs Actual spent (`$14,200 / $25,000`).
    - Task Progress bar (`14/24 Tasks Completed (58%)`).
    - Latest ML Risk Badge (`Low`, `Medium`, `High`).
- **Interactions:**
  - Real-time client-side search filtering.
  - Clicking a project card navigates to `/projects/:id`.
  - "+ Create Project" opens modal with inputs: Title, Description, Start Date, Deadline, Budget.
- **States:**
  - *Loading:* Grid of 6 pulsing skeleton cards.
  - *Empty:* *"No projects found matching your search criteria."*

---

### 2.4 Screen 4: Project Details Screen (`/projects/:id`)
- **Purpose:** Comprehensive operational command center for an individual project.
- **Layout:** Two-tier layout: Top summary & Risk Gauge header, followed by tabbed content (Overview, Tasks, Milestones, History).
- **Components & Data Shown:**
  - **Header Banner:**
    - Project Title, Description, and Status badge.
    - Action Bar: "Assess Risk" button (triggers ML prediction), "Edit Project" button.
  - **Risk & Analytics Hero Card:**
    - Visual Gauge: Delay Probability ($0\% - 100\%$) and numerical Risk Score ($0 - 100$).
    - Expected Delay tag: e.g., *"Expected Delay: +5.8 Days"*.
    - Stat Chips: Budget Burn %, Hours Logged vs Estimated.
  - **Milestone Timeline:** Vertical milestone progression with completion checkmarks.
  - **Embedded Task List:** Direct view of project tasks with status toggles.
- **Interactions:**
  - Clicking "Assess Risk" sends POST request to `/api/predict-risk`, animates the gauge, and immediately renders newly generated AI recommendations.
  - Tab switching between "Tasks", "Milestones", and "AI Insights".
- **States:**
  - *Loading:* Shimmer effect on gauge and tables.
  - *Error:* Card showing *"Failed to load project details. [Retry]"*.

---

### 2.5 Screen 5: Tasks Screen (`/tasks`)
- **Purpose:** Granular task list and board view for task creation, assignment, and hours logging.
- **Layout:** Header filter bar followed by a selectable Table or Kanban Board view.
- **Components & Data Shown:**
  - **Filters:** By Project, Assignee, Priority (`Critical`, `High`, `Med`, `Low`), and Status.
  - **Task Row / Card:**
    - Title & Description tooltip.
    - Project Tag.
    - Assignee Avatar and Name.
    - Priority Badge (e.g., Red for `Critical`).
    - Complexity indicator (`Low`, `Medium`, `High`).
    - Hours badge: `Logged / Estimated` (e.g., `12.0 / 16.0 hrs`).
    - Dependency icon (indicates if task has blocking dependencies).
- **Interactions:**
  - Quick status dropdown inside each row to change from `To Do` -> `In Progress` -> `Completed`.
  - Quick-edit modal to update `actual_hours`.
  - "+ Add Task" button opens task creation modal.
- **States:**
  - *Loading:* Skeleton rows.
  - *Empty:* *"No tasks found matching your filters."*

---

### 2.6 Screen 6: Team Analytics Screen (`/team`)
- **Purpose:** Resource utilization and workload balancing monitor.
- **Layout:** Top summary of overall team capacity followed by a grid of Team Member cards with workload progress bars.
- **Components & Data Shown:**
  - **Aggregate Metrics:** Average team utilization, number of overloaded members ($> 100\%$).
  - **Member Workload Card:**
    - Member Name, Role title, Email.
    - Assigned Active Tasks count.
    - Workload Bar: Allocated active hours vs 40-hr capacity (e.g., `52 / 40 hrs (130%)` in red warning).
    - Status badge: `Optimal`, `Underutilized`, or `Overloaded`.
- **Interactions:**
  - Clicking an overloaded member filters the task view to their active tasks to assist with manual task redistribution.
- **States:**
  - *Empty:* *"No team members added yet."*

---

### 2.7 Screen 7: AI Insights & Delay Prediction Screen (`/insights` or Project Tab)
- **Purpose:** Dedicated explainable Data Science view showing ML prediction parameters, feature contributions, and prescriptive recommendations.
- **Layout:** 3-column split view on desktop:
  - Left: Interactive Project Selector & Feature Inspector.
  - Center: Prediction Gauge & Mathematical Breakdown.
  - Right: Prescriptive Action Cards.
- **Components & Data Shown:**
  1. **Prediction Result Panel:**
     - Big Radial Gauge: Delay Probability ($0.68$) and Risk Score ($66/100$ - `Medium Risk`).
     - Expected Delay Metric: `+5.8 Days`.
     - Timestamp of last model evaluation.
  2. **12-Feature Breakdown Table:**
     - Displays every input feature passed to the Random Forest model with its current value (e.g., `avg_workload: 32.5 hrs`, `task_complexity: 2.2`, `deadline_days: 18`).
  3. **Prescriptive Recommendations List:**
     - Color-coded action cards (Red for urgent, Amber for cautionary, Blue for advisory).
     - Each card displays Title, Rationale, and Suggested Action:
       - *Card 1:* "Redistribute Tasks: Bob Chen is at 130% workload."
       - *Card 2:* "Prioritize 4 Blocking Tasks: Unblock critical dependencies."
       - *Card 3:* "Monitor 18-Day Delivery Runway."
- **Interactions:**
  - "Run Live What-If Simulation" toggle: Allows adjusting sliders (e.g., add 1 team member or reduce tasks) and recalculating risk dynamically in real-time.
- **States:**
  - *Initial / Uncomputed:* *"Click 'Assess Project Risk' to run the Random Forest delay prediction model."*
  - *Loading:* Smooth progress bar animation with step indicators (*"Extracting operational features... Running Random Forest inference... Evaluating heuristic rules..."*).

---

## 3. Responsive Breakpoints & Accessibility

| Viewport Width | Device Category | UI Adaptations |
| :--- | :--- | :--- |
| **$< 768\text{px}$** | Mobile Phones | Full-width single-column layout. Sidebar collapses into top navbar drawer. Tables convert into stacked cards. |
| **$768\text{px} - 1023\text{px}$** | Tablets / Small Laptops | Two-column grid layouts. Sidebar collapses into icon-only rail or drawer. |
| **$\ge 1024\text{px}$** | Desktops & Laptops | Full multi-column layout with expanded sidebar and persistent dashboard widgets. |

- **Color Accessibility:** All status badges pair color fills with distinct text labels and SVG icons to ensure clarity for color-blind users.
- **Keyboard Navigation:** All interactive modals and form fields support full tab indexing and Escape key dismissal.
