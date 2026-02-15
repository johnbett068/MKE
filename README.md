📘 Making Life Easier – African Super App (Backend Blueprint)
🚀 Project Overview

Making Life Easier is a unified African super-app backend designed to simplify daily life by combining transport, delivery, commerce, housing, and jobs into one scalable platform.

The backend is built with Django + Django REST Framework, designed for Flutter mobile clients, and optimized for real African operational realities (cash, verification, multi-role users).

🎯 Core Objectives

One account → multiple roles

Transparent pricing & commissions

Cash + digital payments

Strong verification & trust system

Modular services with shared core logic

Scalable from town-level to national level

👤 System Roles (Actors)

All users share a single Account model and may hold multiple roles:

Customer

Driver / Delivery Agent

Merchant (Shop Owner)

Property Owner / Agent

Employer

Admin

Support (future)

Roles are approved, activated, and verified independently.

🏗️ System Architecture
Core Modules (Shared)

Accounts & Authentication

Roles & Permissions

Profiles

Location Engine

Wallets & Transactions

Verification

Ratings

Notifications

Admin Controls

Service Modules (Pluggable)

Ride Hailing

Delivery & Logistics

Shops & Products

Housing & Rentals

Jobs & Gigs

Marketplace (Buy & Sell)

All service modules depend on the same Account, Wallet, and Location core models.

🌍 Location System

Hierarchical, normalized location structure:

Country

County / Region

Town / City

Zone / Area

Latitude / Longitude

All services reference Location IDs, never free text.

💰 Wallet & Payments Design
Wallet Types

Platform Wallet

Customer Wallet

Driver Wallet (available / pending / debt)

Merchant Wallet

Property Owner Wallet

Payment Rules

Customer always pays the platform first

Platform deducts commission automatically

Provider receives net amount in wallet

Cash Handling

Cash supported from day one

Platform commission recorded as wallet debt

Withdrawals blocked until debt is cleared

Revenue Streams

Ride commission

Delivery commission

Shop order commission

Housing booking fees

Job posting fees

Featured listings

Withdrawal fees

🔒 Trust & Verification System

Verification levels apply per account, not per role:

Level 0 – Unverified

Level 1 – Phone verified

Level 2 – National ID verified

Level 3 – Vehicle / Business verified

Each service defines its minimum required verification level.

🗂 Core Data Models (Locked Design)

These models are mandatory and global:

Account

Role

AccountRole

Profile

Location

Wallet

Transaction

Verification

Rating

Notification

🛵 Service-Specific Models
Rides & Delivery

Vehicle

Trip

TripEvent (optional)

Shops

Shop

Product

Order

OrderItem

Housing

Property

Booking

Jobs

Job

Application

Marketplace

Listing

🔄 Core System Flows
Ride / Delivery

Request service

Fare calculation

Payment or cash recording

Driver assignment

Trip completion

Wallet split

Ratings

Payment Flow

Customer → Platform → Provider

🖥️ Admin Capabilities

Approve users & roles

Manage commissions

Monitor wallets & transactions

Resolve disputes

Suspend accounts

View analytics

💻 Technology Stack
Backend

Django

Django REST Framework

PostgreSQL

Simple JWT

CORS Headers

Mobile

Flutter (Android-first)

Maps

Google Maps (initial)

OpenStreetMap (future)

Payments

M-Pesa

Cards

Cash (recorded)

🧱 Build Strategy

Phase 1: Accounts, Wallets, Rides & Delivery

Phase 2: Shops & Commerce

Phase 3: Housing & Rentals

Phase 4: Jobs & Marketplace

Phase 5: AI Routing & Voice Input

🏛 Architecture Choice

Monolithic Django backend (v1)

Modular apps for future service extraction

📦 Section 9 — Core Data Models (Design Locked)
9.1 Account

Central identity

Email login

Phone login

Google login

One account → multiple roles

9.2 Role

Customer

Driver

Merchant

Property Owner

Employer

Admin

Support

9.3 AccountRole

Links Account ↔ Role

Approval status

Activation control

9.4 Profile

Personal details

Avatar

Contact info

Default location

Verification level

9.5 Location

Country → County → Town → Zone

Latitude / Longitude

9.6 Wallet

Balance

Pending

Debt (cash commissions)

9.7 Transaction

Immutable ledger

Credit / debit

Service type

Reference ID

Full audit trail

9.8 Verification

Phone

National ID

Vehicle

Business

Admin-approved

9.9 Rating

Account → Account

Score (1–5)

Comment

9.10 Notification

Ride updates

Order updates

Wallet alerts

Admin messages

✅ Section 9 Status: Design finalized, no service logic implemented yet.

🔐 Section 10 — Authentication & Login Flow (Design Locked)
Supported Login Methods

Email + Password

Phone + Password (OTP)

Google Sign-In (+ mandatory phone)

Identity Rule

Email OR phone acts as identifier

No duplicate accounts allowed

Default Role

Customer role assigned at signup

Other roles require verification + admin approval

Token Strategy

JWT (access + refresh)

Sent via Authorization: Bearer <token>

✅ Section 10 Status: Authentication flow fully defined, ready for coding.

⚙️ Section 11 — Django Project Setup (Completed)
Completed

Virtual environment

Django + DRF installed

PostgreSQL configured

Custom user model enabled

JWT & CORS configured

Core & service apps created

✅ Section 11 Status: Backend ready for model implementation.

📘 Section 12 — Accounts, Roles & Profiles (Implemented)
Implemented

Custom Account model

Role model

AccountRole (many-to-many)

Profile with verification level

Admin registration

PostgreSQL migrations successful

✅ Section 12 Status: Core user system complete.

🔑 Section 13 — JWT Authentication & API Setup (Implemented)
Implemented

Simple JWT configuration

Token obtain & refresh endpoints

Protected /api/accounts/me/ endpoint

DRF serializers & views

Flutter-compatible auth flow

✅ Section 13 Status: Secure authentication live and tested.

📦 Section 14 — Location System (Core Dependency) (Implemented)

The Location system is a **shared, mandatory dependency** for all services (rides, delivery, shops, housing, jobs).

Free-text locations are **not allowed**.  
All services must reference a normalized Location ID.

---

### 14.1 Location Design Principles

- Hierarchical structure
- Reusable across all modules
- Supports rural + urban African realities
- Enables distance calculations & zoning logic

---

### 14.2 Location Hierarchy

Country  
→ County / Region  
→ Town / City  
→ Zone / Area  

Each level is optional depending on the use case, but **IDs are always used**, never strings.

---

### 14.3 Location Model

```python
# core/models.py

from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children"
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.name

🟣 SECTION 15 — Wallets & Transactions (Core Financial Engine)

This section defines the **financial backbone** of the Making Life Easier platform.
Every payment, commission, cash record, and withdrawal passes through this system.

⚠️ This is a **core module** — ALL services depend on it.

---

## 15.1 Design Principles

- Platform-first payment flow
- Immutable transaction ledger
- Cash + digital payments supported
- Commission handled automatically
- Full auditability (no silent balance changes)
- African cash-reality compliant

---

## 15.2 Wallet Concept

Every account-role combination owns a wallet.

A wallet does NOT represent a bank account —  
it represents a **ledger-controlled balance** managed by the platform.

---

## 15.3 Wallet Types

Each wallet belongs to:
- One Account
- One Role

### Wallet Categories
- Platform Wallet
- Customer Wallet
- Driver Wallet
- Merchant Wallet
- Property Owner Wallet

---

## 15.4 Wallet Balances

Each wallet tracks **three balances**:

- **available_balance**
  - Spendable / withdrawable funds

- **pending_balance**
  - Funds held during active services

- **debt_balance**
  - Cash commission owed to platform

⚠️ Withdrawals are blocked if `debt_balance > 0`

---

## 15.5 Wallet Model

```python
# wallets/models.py
from django.db import models
from accounts.models import Account, Role

class Wallet(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='wallets')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pending_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    debt_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('account', 'role')

    def __str__(self):
        return f"{self.account.email} - {self.role.name} Wallet"

15.6 Transaction Model

Transactions provide the immutable financial ledger of the platform.

Wallet balances should never exist without transaction history.
Every credit or debit must generate a transaction record.

This enables:

Financial audits

Dispute resolution

Fraud detection

Revenue reconciliation

Provider earnings transparency

Transaction Model Structure
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    service = models.CharField(max_length=50)
    reference_id = models.CharField(max_length=100)

    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

15.7 Wallet Service Layer (Critical Business Logic)

All financial operations are centralized in:

wallets/services.py


⚠️ Wallet balances must never be modified directly from views, signals, or external modules.

This ensures:

Financial consistency

Security against double spending

Centralized commission logic

Easier auditing and testing

Core Wallet Operations
Wallet Credit

Used when:

Trips or deliveries complete

Orders are settled

Refunds issued

Admin adjustments made

B