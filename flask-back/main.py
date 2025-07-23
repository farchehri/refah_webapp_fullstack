from flask import Flask, request, jsonify
from flask_cors import CORS # Import CORS
import os
import google.generativeai as genai
from google.cloud import bigquery
import pandas as pd

app = Flask(__name__)
CORS(app) # Enable CORS for all origins. Consider restricting this in production.

# === CONFIGURATION ===
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- BIGQUERY CONFIGURATION ---
PROJECT_ID = "gemini-web-agent-466416"
DATASET_ID = "Refah_CSV"
TABLE_ID = "table_CSV_Mapped_1000"
FULL_TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# Define your BigQuery table schema for Gemini's context
BIGQUERY_TABLE_SCHEMA = """
جدول 'table_CSV_Mapped_1000' در مجموعه داده 'Refah_CSV' شامل اطلاعات اجتماعی-اقتصادی و داده‌های تراکنش‌های مالی افراد است.
هر ردیف نماینده یک فرد منحصر به فرد است.

در ادامه طرحواره جدول با نام ستون‌ها، نوع داده‌های BigQuery و توضیحات تفصیلی آورده شده است:

- `id` (INTEGER): شناسه یکتای هر فرد.
- `head_id` (STRING): شناسه سرپرست خانوار برای هر فرد.
- `hadafmandi` (INTEGER): نشان می‌دهد آیا فرد در طرح هدفمندی یارانه‌های دولتی ثبت‌نام شده است (0=خیر, 1=بله).
- `subsidy_cash` (INTEGER): نشان می‌دهد آیا فرد یارانه نقدی دولتی دریافت می‌کند (0=خیر, 1=بله).
- `age` (FLOAT): سن فرد بر حسب سال.
- `gender` (INTEGER): جنسیت فرد (1=مرد, 2=زن).
- `urban` (INTEGER): نوع محل سکونت (1=شهری, 0=روستایی).
- `behzisti` (INTEGER): نشان می‌دهد آیا فرد تحت پوشش سازمان بهزیستی است (0=خیر, 1=بله).
- `emdad` (INTEGER): نشان می‌دهد آیا فرد تحت پوشش کمیته امداد امام خمینی است (0=خیر, 1=بله).
- `disabled` (INTEGER): نشان می‌دهد آیا فرد دارای معلولیت است (0=خیر, 1=بله).
- `special_disease` (INTEGER): نشان می‌دهد آیا فرد بیماری خاص دارد (0=خیر, 1=بله).
- `shaparak_monthly_1400_avg` (FLOAT): میانگین ماهانه مبلغ خرید با کارت (POS/شاپرک) در سال 1400 شمسی.
- `shaparak_monthly_1401_avg` (FLOAT): میانگین ماهانه مبلغ خرید با کارت (POS/شاپرک) در سال 1401 شمسی.
- `shaparak_monthly_1402_avg` (FLOAT): میانگین ماهانه مبلغ خرید با کارت (POS/شاپرک) در سال 1402 شمسی.
- `cardtocard_monthly_1401_avg` (FLOAT): میانگین ماهانه مبلغ انتقال از کارت به کارت در سال 1401 شمسی.
- `cardtocard_monthly_1402_avg` (FLOAT): میانگین ماهانه مبلغ انتقال از کارت به کارت در سال 1402 شمسی.
- `paya_monthly_1401_avg` (FLOAT): میانگین ماهانه مبلغ انتقالات پایا در سال 1401 شمسی.
- `paya_monthly_1402_avg` (FLOAT): میانگین ماهانه مبلغ انتقالات پایا در سال 1402 شمسی.
- `satna_monthly_1401_avg` (FLOAT): میانگین ماهانه مبلغ انتقالات ساتنا (انتقالات با مبلغ بالا) در سال 1401 شمسی.
- `satna_monthly_1402_avg` (FLOAT): میانگین ماهانه مبلغ انتقالات ساتنا (انتقالات با مبلغ بالا) در سال 1402 شمسی.
- `pos_monthly_1401_avg` (FLOAT): میانگین ماهانه مبلغ واریزی به حساب‌های POS (دستگاه کارتخوان) در سال 1401 شمسی.
- `pos_monthly_1402_avg` (FLOAT): میانگین ماهانه مبلغ واریزی به حساب‌های POS (دستگاه کارتخوان) در سال 1402 شمسی.
- `income_total` (FLOAT): مجموع درآمد اعلام شده.
- `bourse_portfolio_value` (FLOAT): ارزش پرتفوی بورسی (سهام و اوراق بهادار).
- `car_total_count` (INTEGER): تعداد کل خودروهای تحت مالکیت.
- `has_household_structure` (INTEGER): نشان می‌دهد آیا اطلاعات ساختار خانوار فرد موجود است (0=خیر, 1=بله).
- `decile` (INTEGER): دهک درآمدی (بین 1 تا 10، که 1 پایین‌ترین و 10 بالاترین دهک است).
- `percentile` (INTEGER): صدک درآمدی (بین 1 تا 100).
- `disabled_severity` (STRING): شدت معلولیت (مثال: 'شدید', 'متوسط', 'خفیف').
- `ostan` (STRING): نام استان محل اقامت.
- `shahrestan` (STRING): نام شهرستان یا شهر محل اقامت.
- `retired_asli` (INTEGER): نشان می‌دهد آیا فرد بازنشسته اصلی است (0=خیر, 1=بله).
- `retired_tabaei` (INTEGER): نشان می‌دهد آیا فرد بازنشسته تبعی است (0=خیر, 1=بله).
- `retired_tamin_asli` (INTEGER): نشان می‌دهد آیا فرد بازنشسته اصلی از صندوق تامین اجتماعی است (0=خیر, 1=بله).
- `retired_tamin_tabaei` (INTEGER): نشان می‌دهد آیا فرد بازنشسته تبعی از صندوق تامین اجتماعی است (0=خیر, 1=بله).
- `retired_keshvari_asli` (INTEGER): نشان می‌دهد آیا فرد بازنشسته اصلی از صندوق بازنشستگی کشوری است (0=خیر, 1=بله).
- `retired_keshvari_tabaei` (INTEGER): نشان می‌دهد آیا فرد بازنشسته تبعی از صندوق بازنشستگی کشوری است (0=خیر, 1=بله).
- `retired_foolad_asli` (INTEGER): نشان می‌دهد آیا فرد بازنشسته اصلی از صندوق بازنشستگی فولاد است (0=خیر, 1=بله).
- `retired_foolad_tabaei` (INTEGER): نشان می‌دهد آیا فرد بازنشسته تبعی از صندوق بازنشستگی فولاد است (0=خیر, 1=بله).
- `retired_homa_asli` (INTEGER): نشان می‌دهد آیا فرد بازنشسته اصلی از صندوق بازنشستگی هما (هواپیمایی) است (0=خیر, 1=بله).
- `retired_homa_tabaie` (INTEGER): نشان می‌دهد آیا فرد بازنشسته تبعی از صندوق بازنشستگی هما (هواپیمایی) است (0=خیر, 1=بله).
- `retired_shahrdari_asli` (INTEGER): نشان می‌دهد آیا فرد بازنشسته اصلی از صندوق بازنشستگی شهرداری است (0=خیر, 1=بله).
- `retired_shahrdari_tabaie` (INTEGER): نشان می‌دهد آیا فرد بازنشسته تبعی از صندوق بازنشستگی شهرداری است (0=خیر, 1=بله).
- `retired_banader_asli` (INTEGER): نشان می‌دهد آیا فرد بازنشسته اصلی از صندوق بازنشستگی بنادر است (0=خیر, 1=بله).
- `retired_banader_tabaei` (INTEGER): نشان می‌دهد آیا فرد بازنشسته تبعی از صندوق بازنشستگی بنادر است (0=خیر, 1=بله).
- `retired_kanonvokala_asli` (INTEGER): نشان می‌دهد آیا فرد بازنشسته اصلی از صندوق کانون وکلای دادگستری است (0=خیر, 1=بله).
- `retired_kanonvokala_tabaei` (INTEGER): نشان می‌دهد آیا فرد بازنشسته تبعی از صندوق کانون وکلای دادگستری است (0=خیر, 1=بله).
- `retired_bank_asli` (INTEGER): نشان می‌دهد آیا فرد بازنشسته اصلی از صندوق بازنشستگی بانک‌ها است (0=خیر, 1=بله).
- `retired_bank_tabaei` (INTEGER): نشان می‌دهد آیا فرد بازنشسته تبعی از صندوق بازنشستگی بانک‌ها است (0=خیر, 1=بله).
- `retired_roosta_asli` (INTEGER): نشان می‌دهد آیا فرد بازنشسته اصلی از صندوق بیمه اجتماعی روستاییان و عشایر است (0=خیر, 1=بله).
- `retired_roosta_tabaie` (INTEGER): نشان می‌دهد آیا فرد بازنشسته تبعی از صندوق بیمه اجتماعی روستاییان و عشایر است (0=خیر, 1=بله).
- `retired_bimemarkazi_asli` (INTEGER): نشان می‌دهد آیا فرد بازنشسته اصلی از صندوق بیمه مرکزی است (0=خیر, 1=بله).
- `retired_bimemarkazi_tabaei` (INTEGER): نشان می‌دهد آیا فرد بازنشسته تبعی از صندوق بیمه مرکزی است (0=0=خیر, 1=بله).
- `retired_sedasima_asli` (INTEGER): نشان می‌دهد آیا فرد بازنشسته اصلی از صندوق بازنشستگی صدا و سیما است (0=خیر, 1=بله).
- `retired_ayandesaz_asli` (INTEGER): نشان می‌دهد آیا فرد بازنشسته اصلی از صندوق بازنشستگی آینده‌ساز است (0=خیر, 1=بله).
- `retired_ayandesaz_tabaei` (INTEGER): نشان می‌دهد آیا فرد بازنشسته تبعی از صندوق بازنشستگی آینده‌ساز است (0=خیر, 1=بله).
- `employed` (INTEGER): نشان می‌دهد آیا فرد شاغل است (0=خیر, 1=بله).
- `employed_tamin` (INTEGER): نشان می‌دهد آیا فرد بیمه‌پرداز صندوق تامین اجتماعی است (0=خیر, 1=بله).
- `employed_tamin_mashaghelazad` (INTEGER): نشان می‌دهد آیا فرد بیمه‌پرداز آزاد صندوق تامین اجتماعی است (0=خیر, 1=بله).
- `employed_tamin_mashaghelekhtiari` (INTEGER): نشان می‌دهد آیا فرد بیمه‌پرداز اختیاری صندوق تامین اجتماعی است (0=خیر, 1=بله).
- `employed_keshvari` (INTEGER): نشان می‌دهد آیا فرد بیمه‌پرداز صندوق کشوری است (0=خیر, 1=بله).
- `employed_khazane` (INTEGER): نشان می‌دهد آیا فرد شاغل است و حقوق او از طریق خزانه پرداخت می‌شود (0=خیر, 1=بله).
- `employed_edariestekhdami` (INTEGER): نشان می‌دهد آیا فرد شاغل دارای استخدام اداری است (0=خیر, 1=بله).
- `employed_foolad` (INTEGER): نشان می‌دهد آیا فرد بیمه‌پرداز صندوق فولاد است (0=خیر, 1=بله).
- `employed_kanonvokala` (INTEGER): نشان می‌دهد آیا فرد بیمه‌پرداز صندوق کانون وکلای دادگستری است (0=خیر, 1=بله).
- `employed_bank` (INTEGER): نشان می‌دهد آیا فرد بیمه‌پرداز صندوق بانک است (0=خیر, 1=بله).
- `employed_roosta` (INTEGER): نشان می‌دهد آیا فرد بیمه‌پرداز صندوق روستاییان و عشایر است (0=خیر, 1=بله).
- `employed_bimemarkazi` (INTEGER): نشان می‌دهد آیا فرد بیمه‌پرداز صندوق بیمه مرکزی است (0=خیر, 1=بله).
- `employed_maliat_hoghogh` (INTEGER): نشان می‌دهد آیا فرد شاغل است و مالیات بر حقوق می‌پردازد (0=خیر, 1=بله).
- `employed_maliat_daramadmashaghel` (INTEGER): نشان می‌دهد آیا فرد شاغل است و مالیات بر درآمد مشاغل می‌پردازد (0=خیر, 1=بله).
- `employed_ayandesaz` (INTEGER): نشان می‌دهد آیا فرد بیمه‌پرداز صندوق آینده‌ساز است (0=خیر, 1=بله).
- `employed_vezarat_behdasht` (INTEGER): نشان می‌دهد آیا فرد شاغل وزارت بهداشت است (0=خیر, 1=بله).
- `medical_insurance` (INTEGER): نشان می‌دهد آیا فرد دارای بیمه درمانی است (0=خیر, 1=بله).
- `medical_insurance_insurer` (STRING): نام شرکت بیمه‌کننده درمانی.
- `medical_insurance_product` (STRING): نوع محصول بیمه درمانی.
- `loan_1400` (FLOAT): مجموع مبلغ وام دریافتی در سال 1400 شمسی.
- `loan_1401` (FLOAT): مجموع مبلغ وام دریافتی در سال 1401 شمسی.
- `AMT_1_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'اثاث و تجهیزات الکترونیکی خانگی'.
- `AMT_2_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'دارو و تجهیزات پزشکی'.
- `AMT_3_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'اجاره و تعمیر اثاثیه'.
- `AMT_4_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'انتشارات و لوازم التحریر'.
- `AMT_5_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'پوشاک'.
- `AMT_6_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'ساخت، تعمیر و نگهداری ساختمان'.
- `AMT_7_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'نانوایی'.
- `AMT_8_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'خدمات ارتباط و حمل و نقل'.
- `AMT_9_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'خدمات آموزش و مشاوره'.
- `AMT_10_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'خدمات درمانی و بهداشتی'.
- `AMT_11_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'خدمات تهیه و ارائه غذا'.
- `AMT_12_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'خدمات بخش عمومی'.
- `AMT_13_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'خدمات وسایل نقلیه'.
- `AMT_14_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'کالا و خدمات لوکس، خاص و زیبایی'.
- `AMT_15_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'تامین مواد اولیه و زنجیره تامین'.
- `AMT_16_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'سوپرمارکت، خواربارفروشی'.
- `AMT_17_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'کالا و خدمات دیجیتال'.
- `AMT_18_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'کالا و خدمات تفریحی، گردشگری و هنری'.
- `AMT_19_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'خدمات کسب و کار'.
- `AMT_20_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'مالی'.
- `AMT_21_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'مالیات'.
- `AMT_22_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'متفرقه'.
- `AMT_23_1401_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1401 شمسی از صنف 'مذهبی و عام‌المنفعه'.
- `AMT_1_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'اثاث و تجهیزات الکترونیکی خانگی'.
- `AMT_2_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'دارو و تجهیزات پزشکی'.
- `AMT_3_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'اجاره و تعمیر اثاثیه'.
- `AMT_4_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'انتشارات و لوازم التحریر'.
- `AMT_5_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'پوشاک'.
- `AMT_6_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'ساخت، تعمیر و نگهداری ساختمان'.
- `AMT_7_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'نانوایی'.
- `AMT_8_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'خدمات ارتباط و حمل و نقل'.
- `AMT_9_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'خدمات آموزش و مشاوره'.
- `AMT_10_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'خدمات درمانی و بهداشتی'.
- `AMT_11_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'خدمات تهیه و ارائه غذا'.
- `AMT_12_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'خدمات بخش عمومی'.
- `AMT_13_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'خدمات وسایل نقلیه'.
- `AMT_14_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'کالا و خدمات لوکس، خاص و زیبایی'.
- `AMT_15_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'تامین مواد اولیه و زنجیره تامین'.
- `AMT_16_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'سوپرمارکت، خواربارفروشی'.
- `AMT_17_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'کالا و خدمات دیجیتال'.
- `AMT_18_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'کالا و خدمات تفریحی، گردشگری و هنری'.
- `AMT_19_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'خدمات کسب و کار'.
- `AMT_20_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'مالی'.
- `AMT_21_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'مالیات'.
- `AMT_22_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'متفرقه'.
- `AMT_23_1401_0612` (FLOAT): مبلغ خرید کارتی در 6 ماه دوم (مهر تا اسفند) سال 1401 شمسی از صنف 'مذهبی و عام‌المنفعه'.
- `AMT_1_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'اثاث و تجهیزات الکترونیکی خانگی'.
- `AMT_2_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'دارو و تجهیزات پزشکی'.
- `AMT_3_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'اجاره و تعمیر اثاثیه'.
- `AMT_4_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'انتشارات و لوازم التحریر'.
- `AMT_5_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'پوشاک'.
- `AMT_6_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'ساخت، تعمیر و نگهداری ساختمان'.
- `AMT_7_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'نانوایی'.
- `AMT_8_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'خدمات ارتباط و حمل و نقل'.
- `AMT_9_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'خدمات آموزش و مشاوره'.
- `AMT_10_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'خدمات درمانی و بهداشتی'.
- `AMT_11_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'خدمات تهیه و ارائه غذا'.
- `AMT_12_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'خدمات بخش عمومی'.
- `AMT_13_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'خدمات وسایل نقلیه'.
- `AMT_14_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'کالا و خدمات لوکس، خاص و زیبایی'.
- `AMT_15_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'تامین مواد اولیه و زنجیره تامین'.
- `AMT_16_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'سوپرمارکت، خواربارفروشی'.
- `AMT_17_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'کالا و خدمات دیجیتال'.
- `AMT_18_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'کالا و خدمات تفریحی، گردشگری و هنری'.
- `AMT_19_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'خدمات کسب و کار'.
- `AMT_20_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'مالی'.
- `AMT_21_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'مالیات'.
- `AMT_22_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'متفرقه'.
- `AMT_23_1402_0106` (FLOAT): مبلغ خرید کارتی در 6 ماه اول (فروردین تا شهریور) سال 1402 شمسی از صنف 'مذهبی و عام‌المنفعه'.
"""

# === GLOBAL STATE (lazy init on first /ask) ===
model = None
chat = None
bigquery_client = None
initialized = False

# === FLASK ROUTES ===

# Remove the old render_template route for the SPA
# @app.route("/")
# def index():
#     return render_template("index.html")

# Add a simple health check or info route for the API
@app.route("/")
def health_check():
    """Returns a simple JSON response to indicate the API is running."""
    return jsonify({"status": "API is running", "message": "Connect your React frontend to /chat"}), 200

@app.route("/test")
def test_route():
    """Returns a simple JSON response to indicate the API is running."""
    return jsonify({"status": "API is running", "message": " the app route is working f ok! "}), 200


@app.route("/chat", methods=["POST"])
def chat():
    global model, chat, bigquery_client, initialized

    user_question = request.json.get("question")
    if not user_question:
        return jsonify({"error": "No question provided"}), 400

    try:
        # === One-time Initialization ===
        if not initialized:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("models/gemini-1.5-pro")

            bigquery_client = bigquery.Client(project=PROJECT_ID)

            chat = model.start_chat()
            chat.send_message(f"""You are a helpful data analyst AI.
You have access to a BigQuery table with the following full ID: `{FULL_TABLE_ID}`.
This is the table schema:
{BIGQUERY_TABLE_SCHEMA}

When I ask a question about the data, your task is to first generate a valid SQL query for BigQuery that answers my question.
**Important:** Do NOT include any backticks or formatting around the SQL query. Just output the raw SQL.
If the question cannot be answered by a single SQL query, state that and then provide a natural language response in persian language. make sure your default language to respond is Persian.
After the SQL, if you have generated one, you should output an indicator like '---SQL_END---'.
Then, after '---SQL_END---', you can provide a natural language explanation or summary of what the query does.
Do NOT execute the query yourself. Only provide the SQL.
""")
            initialized = True
            print("Gemini model and BigQuery client initialized.")

        # === Step 1: Ask Gemini to generate SQL ===
        # Pass the user's direct question to Gemini to get a SQL query
        sql_gen_response = chat.send_message(f"Generate a SQL query to answer: {user_question}")
        gemini_response_text = sql_gen_response.text.strip()

        # Parse Gemini's response to extract SQL
        sql_query = ""
        explanation = ""
        if "---SQL_END---" in gemini_response_text:
            parts = gemini_response_text.split("---SQL_END---", 1)
            sql_query = parts[0].strip()
            explanation = parts[1].strip() if len(parts) > 1 else ""
            print(f"Generated SQL Query: {sql_query}")
        else:
            # If no SQL_END indicator, Gemini decided to give a direct natural language response
            print(f"Gemini provided direct natural language response: {gemini_response_text}")
            return jsonify({"answer": gemini_response_text})

        # Check if Gemini actually provided a SQL query to execute
        if not sql_query:
            print("Gemini did not generate a SQL query.")
            return jsonify({"error": "Gemini could not generate a SQL query for that question or provided a direct answer."}), 400

        # === Step 2: Execute SQL query on BigQuery ===
        print("Executing BigQuery query...")
        job = bigquery_client.query(sql_query)
        query_results = job.result() # Waits for the job to complete
        print("BigQuery query executed successfully.")

        # Format results (using pandas for convenience)
        results_df = query_results.to_dataframe()

        # === Step 3: Send results back to Gemini for summarization (Optional but Recommended) ===
        if not results_df.empty:
            results_csv = results_df.to_csv(index=False)
            summarize_prompt = f"""Based on the following data results from a BigQuery query, and the original question '{user_question}', provide a concise and clear answer to the user in Persian.
The query results are:
---
{results_csv}
---
"""
            print("Sending results to Gemini for summarization...")
            final_answer_response = chat.send_message(summarize_prompt)
            final_answer = final_answer_response.text
            print(f"Final summarized answer from Gemini: {final_answer}")
        else:
            final_answer = "هیچ نتیجه‌ای برای پرسش شما یافت نشد. " + explanation if explanation else "هیچ نتیجه‌ای برای پرسش شما یافت نشد."
            print(f"No results found: {final_answer}")

        return jsonify({"answer": final_answer})

    except Exception as e:
        print(f"Error during /ask: {e}")
        # This will now reliably return JSON errors to the frontend
        return jsonify({"error": str(e)}), 500

# === LOCAL DEBUG ===
if __name__ == "__main__":
    # Specify port 5000 for local development to match React's default proxy target
    app.run(debug=True, port=5000)