# 🤖 ChatGPT Integration Setup

## 🎯 Balloon Domain + ChatGPT Integration

Detta system använder **riktig ChatGPT** för att analysera dokument mot varmluftsballong-kunskapsbasen.

### 📋 Vad som är implementerat:

#### 1. **🎈 Balloon Domain Knowledge Base**
- **20 core topics** - säkerhet, navigation, väder, turism, ekonomi
- **Kvalitetskriterier** - min längd (1000 chars), tröskelvärde (7.0)
- **Relevansvikter** - säkerhet (20%), teknisk djup (25%), praktiskt värde (15%)

#### 2. **🤖 Riktig ChatGPT Integration**
- **OpenAI API** - använder GPT-4o för dokumentanalys
- **Balloon-specialiserad prompt** - expertanalys för varmluftsballonger
- **Fallback till mock** - fungerar även utan API-nyckel
- **JSON-respons** - strukturerad analys med scores och beslut

#### 3. **📊 Intelligent Beslutslogik**
- **Auto-approve** (8.0-10.0): Hög kvalitet, direkt godkänd
- **Human review** (7.0-7.9): Behöver mänsklig granskning  
- **Auto-reject** (0.0-6.9): Låg kvalitet, avvisas

## 🚀 Så här aktiverar du riktig ChatGPT:

### 1. **Sätt OpenAI API-nyckel i root .env fil:**
```bash
# I root .env fil (en nivå ovanför backend/)
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 2. **Testa integrationen:**
```bash
cd backend
uv run python test_balloon_ai_integration.py
```

### 3. **Kör med riktig ChatGPT:**
- **Med API-nyckel** → Riktig ChatGPT-analys
- **Utan API-nyckel** → Mock-analys (fungerar ändå)

## 📊 Testresultat:

### **Mock Analysis (utan API-nyckel):**
```
📈 Relevance score: 6.83
✅ Is relevant: False
🎯 Decision: Auto-reject (low quality)
🔍 Quality indicators:
   safety_focus: 0.74
   technical_depth: 0.75
   practical_value: 0.98
```

### **Real ChatGPT Analysis (med API-nyckel):**
- Får riktig AI-analys av dokumentinnehåll
- Balloon-specialiserad prompt för expertbedömning
- Strukturerad JSON-respons med scores och beslut

## 🔧 Konfiguration:

### **Balloon Domain Criteria:**
```python
# config/balloon_criteria.py
CORE_TOPICS = [
    "hot air balloon", "balloon flight", "balloon navigation", 
    "balloon safety", "balloon weather", "balloon tourism",
    "balloon economics", "balloon history", "balloon science",
    "balloon technology", "balloon piloting", "balloon maintenance",
    "balloon regulations", "balloon equipment", "balloon materials",
    "balloon physics", "balloon meteorology", "balloon engineering",
    "balloon design", "balloon operations"
]

QUALITY_CRITERIA = {
    "min_length": 1000,
    "quality_threshold": 7.0,
    "required_sections": ["abstract", "introduction", "conclusion", "references"],
    "technical_depth_required": True,
    "safety_considerations_required": True,
    "practical_applications_required": True
}
```

### **AI Analysis Prompt:**
```
You are an expert analyst specializing in hot air balloon knowledge and operations.
Your task is to analyze documents for relevance to the hot air balloon domain.

DOMAIN FOCUS: Hot Air Balloon Knowledge Base
- Balloon operations and piloting
- Safety protocols and procedures  
- Weather and navigation systems
- Tourism and economic impact
- Historical and scientific aspects
- Technology and equipment
- Regulations and compliance

ANALYSIS CRITERIA:
1. TOPIC RELEVANCE (30%): How directly does this relate to hot air balloons?
2. TECHNICAL ACCURACY (25%): Are technical details correct and detailed?
3. SAFETY FOCUS (20%): Does it address safety considerations?
4. PRACTICAL VALUE (15%): Will this help balloon operations?
5. COMPLETENESS (10%): Is the information comprehensive?

SCORING SCALE: 0.0 - 10.0
- 8.0-10.0: Excellent, auto-approve
- 7.0-7.9: Good, needs human review  
- 0.0-6.9: Poor, auto-reject
```

## 🧪 Testning:

### **Test Balloon AI Integration:**
```bash
cd backend
uv run python test_balloon_ai_integration.py
```

### **Test Document Learning:**
```bash
cd backend
uv run python test_document_learning.py
```

### **Test med riktiga dokument:**
```bash
# Test med balloon-article-1.txt, balloon-article-2.txt, balloon-article-3.txt
just document-learning-test
```

## 📈 Resultat:

### **Balloon Domain Configuration:**
- ✅ **20 topics** konfigurerade
- ✅ **Quality threshold** 7.0
- ✅ **Min length** 1000 characters
- ✅ **10 quality indicators**

### **AI Analysis:**
- ✅ **Mock analysis** fungerar (fallback)
- ✅ **Real ChatGPT** redo (med API-nyckel)
- ✅ **Decision logic** korrekt
- ✅ **Quality indicators** visar säkerhet, teknisk djup, praktiskt värde

## 🎯 Nästa steg:

1. **Sätt OPENAI_API_KEY** i root .env fil
2. **Testa med riktig ChatGPT** 
3. **Integrera med Temporal workflows**
4. **Bygg HITL controller interface**

## 🔍 Felsökning:

### **"OPENAI_API_KEY not set":**
- Kontrollera att API-nyckeln är satt i root .env fil
- Kör `cat ../.env | grep OPENAI_API_KEY`

### **"OpenAI client not available":**
- Installera OpenAI: `uv add openai`
- Kontrollera att API-nyckeln är giltig

### **"Mock analysis fallback":**
- Detta är normalt utan API-nyckel
- Mock-analys fungerar för testning
- Sätt API-nyckel för riktig ChatGPT
