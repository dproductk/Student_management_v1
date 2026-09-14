<!-- Page 1 -->

EDVANA MIS - Screen Inventory v1.0
Reference: Reverse-engineered from the provided EDVANA screenshots ZIP. This
inventory serves as a navigation blueprint for recreating the prototype.
Project Summary
Screens analyzed: 86
Portals: Student Portal, Faculty Portal
Authentication screens missing and will be designed separately (Login, Forgot
Password, Reset Password, First Login Password Change, CAPTCHA, Session Expired,
Unauthorized).
Student Portal Modules
• Dashboard
• Navigation / Sidebar
• Profile (Personal, Contact, Address, Guardian, Qualification, Aadhaar, Bank, Photo,
Signature)
• Admission Fee
• Payment History
• Exam Registration (Regular & Backlog)
• Faculty Feedback
• Hall Ticket
• Online Exam
• Duplicate ID Card
• Results
• Change Password
Estimated Coverage: ~95%
Faculty Portal Modules
• Dashboard
• Profile
• Student Management
• Admission Management
• Workload
• Internal Marks
• Detention
• Online Examination
• Result Analysis
• Result History
• Change Password
Estimated Coverage: ~90–95%
Reusable Layouts
1. Authentication Layout
2. Student Dashboard Layout

---

<!-- Page 2 -->

3. Faculty Dashboard Layout
4. Form Layout
5. Table Layout
Reusable Components
Sidebar, Navbar, Breadcrumb, Dashboard Cards, Profile Cards, Forms, Upload
Components,
Data Tables, Search, Filters, Pagination, Status Badges, Dialogs, Toasts,
Loading States, Empty States.
Implementation Order
1. Authentication
2. Shared Layout
3. Shared Components
4. Student Dashboard
5. Student Profile
6. Admission Fee
7. Payment History
8. Exam Registration
9. Faculty Feedback
10. Results
11. Duplicate ID
12. Online Exam
13. Faculty Dashboard
14. Faculty Profile
15. Student Management
16. Admission
17. Workload
18. Marks Entry
19. Detention
20. Result Analysis
21. Reports
22. Admin Portal
Recommendation
Create a second document called 'Page Manifest' with one page per screen,
documenting route,
UI elements, fields, table columns, validations, APIs, entities and reusable components.
This will become the implementation blueprint.
