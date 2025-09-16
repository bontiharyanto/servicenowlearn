# ServiceNow Documentation

> Catatan belajar & implementasi ServiceNow. Gunakan sebagai living document—update seiring progres.

## Daftar Isi
- [1. Pendahuluan](#1-pendahuluan)
- [2. Konsep Dasar & Terminologi](#2-konsep-dasar--terminologi)
- [3. ITSM](#3-itsm)
  - [3.1 Incident Management](#31-incident-management)
  - [3.2 Problem Management](#32-problem-management)
  - [3.3 Change Enablement](#33-change-enablement)
- [4. ITOM (Pengantar)](#4-itom-pengantar)
  - [4.1 CMDB & Discovery](#41-cmdb--discovery)
  - [4.2 Event Management](#42-event-management)
- [5. Integrasi & Otomasi](#5-integrasi--otomasi)
  - [5.1 REST API & Scripted REST](#51-rest-api--scripted-rest)
  - [5.2 Flow Designer](#52-flow-designer)
- [6. Praktik Terbaik](#6-praktik-terbaik)
  - [6.1 Penamaan & Konvensi Kode](#61-penamaan--konvensi-kode)
  - [6.2 Branching, Commit, & Release](#62-branching-commit--release)
  - [6.3 Pengujian](#63-pengujian)
- [7. Deployment & Migrasi](#7-deployment--migrasi)
- [8. Keamanan & Akses](#8-keamanan--akses)
- [9. Runbook Ringkas](#9-runbook-ringkas)
- [10. Glosarium](#10-glosarium)
- [11. Referensi](#11-referensi)

---

## 1. Pendahuluan
Dokumen ini merangkum pembelajaran ServiceNow untuk skenario umum: manajemen insiden, problem, change, CMDB/Discovery, serta integrasi ringan.  
Target pembaca: engineer/analyst yang baru memulai namun ingin cepat produktif.

## 2. Konsep Dasar & Terminologi
- **Record**: baris data dalam tabel (contoh: `incident`).
- **Table**: skema data (turunan dari `task` untuk banyak proses ITSM).
- **Form & List**: tampilan record dan daftar record.
- **Update Set / App Repo**: mekanisme memindahkan konfigurasi antar environment.
- **Scope**: ruang lingkup aplikasi (global vs scoped app).
- **ACL (Access Control List)**: kontrol akses berbasis record/field/operation.

---

## 3. ITSM

### 3.1 Incident Management
**Tujuan**: mengembalikan layanan normal secepatnya dan meminimalkan dampak bisnis.  
**Alur standar**:
1. *Log* → buat incident (sumber: portal, email, integrasi)  
2. *Triage* → klasifikasikan (kategori, prioritas via impact × urgency)  
3. *Assign* → ke assignment group/assignee  
4. *Investigate* → diagnosa & workaround  
5. *Resolve* → solusi diterapkan  
6. *Close* → verifikasi pengguna; isi *closure code/notes*  

**Tips konfigurasi**:
- Otomatiskan prioritas (BR/Flow) berdasar CI & layanan terdampak.
- Template incident untuk kasus berulang.
- SLAs: *response* & *resolution* berbasis prioritas.

### 3.2 Problem Management
- Tautkan **incident** berulang ke **problem**.
- Root Cause Analysis (RCA) → gunakan *Known Error* base.
- *Change* bisa dibuat dari *problem* untuk perbaikan permanen.

### 3.3 Change Enablement
- Tipe: *Standard* (pre-approved), *Normal*, *Emergency*.
- Workflow: *Plan → Assess → Approve (CAB) → Implement → Review → Close*.
- Integrasi kalender rilis & blackout windows.

---

## 4. ITOM (Pengantar)

### 4.1 CMDB & Discovery
- **CMDB**: sumber kebenaran CI (Configuration Item) & relasi.
- **Discovery**: menemukan perangkat/aplikasi (via MID Server).
- Atur **Identification & Reconciliation** untuk mencegah duplikasi.
- Kualitas CMDB: ukur dengan *completeness, correctness, compliance*.

### 4.2 Event Management
- Konsumsi event dari tool monitoring → buat alert → korelasi → *auto-ticketing* opsional (Incident/Task).
- Gunakan *alert aggregation* untuk mengurangi noise.

---

## 5. Integrasi & Otomasi

### 5.1 REST API & Scripted REST
- **REST Table API**: CRUD terhadap tabel (contoh: `incident`).
- **Scripted REST**: endpoint kustom (logika validasi/transformasi).
- Contoh *curl* sederhana (ganti kredensial & instance):
  ```bash
  curl -u user:pass \
    "https://<instance>.service-now.com/api/now/table/incident?sysparm_limit=1"
