# Order to Cash (O2C) Simulation Project

This is a complete end-to-end O2C simulation built with Flask, SQLite, and a browser-based dashboard.

## Workflow
Customer → Product → Sales Order → Credit Approval → Delivery → Invoice → Payment

## Features
- Add customers
- Add products
- Create sales orders
- Approve credit
- Post deliveries
- Generate invoices
- Record payments
- View master data and document overview
- Reset all data

## Project Structure
```text
o2c-project/
├── project/
│   ├── backend/
│   │   └── app.py
│   ├── frontend/
│   │   └── o2c-dashboard.html
│   └── database/
│       └── schema.sql
├── docs/
│   └── project-report.md
└── README.md
```

## How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Open the backend folder and run:
   ```bash
   python app.py
   ```

3. Open the browser:
   ```text
   http://127.0.0.1:5000
   ```

4. Click **Initialize Database**.

## Notes
- The database is stored in SQLite.
- Use unique customer codes and product codes.
- Delivery can be posted only after credit approval.
- Invoice can be created only after delivery.
- Payment can be recorded only after invoice creation.

## Screenshots
<img width="1046" height="648" alt="Screenshot 2026-04-21 192115" src="https://github.com/user-attachments/assets/ca1aac18-c971-41e9-b596-ffecaaee808b" />
<img width="1008" height="639" alt="Screenshot 2026-04-21 192126" src="https://github.com/user-attachments/assets/ff116e66-bb3b-4ac6-93cc-621c9fac8a29" />

##Sample SAP O2C
<img width="464" height="349" alt="image" src="https://github.com/user-attachments/assets/fc771f68-68bf-4e50-9dc4-695d09aec5e1" />
<img width="715" height="333" alt="image" src="https://github.com/user-attachments/assets/e0e39cdb-a35f-4761-89f2-c7fbf73c7acb" />



