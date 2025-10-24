# Design System - hey.sh

Detta dokument definierar det officiella designsystemet för hey.sh. **Dessa regler får INTE brytas.**

## Designfilosofi

**Ljus, professionell terminal-estetik**
- Ljus design med subtila kontraster
- Terminal/Console-tema men modernt och rent
- Konsistens framför allt - ingen sida ska kännas annorlunda

---

## Färgpalett

### Primära färger (HSL)

**Mörkt blått (vårt "svarta")**
- Primary: `215 85% 9%` - Mycket mörkt midnight blue
- Används för: Text, primära knappar, viktig information

**Ljusblått/Cyan (kontrastfärg)**
- Accent: `190 100% 50%` - Terminal cyan
- Används för: Aktiva länkar, hover-states, terminal-ikon, nuvarande sida i breadcrumb
- **VIKTIGT:** Sista elementet i breadcrumb MÅSTE vara i denna färg

**Ljus bakgrund**
- Background: `0 0% 98%` - Ljus ljus grå/silver/blå ton
- Card: `0 0% 100%` - Vit

### Gråblå nyanser (för depth och variation)

```css
--muted: 220 14% 96%;           /* Ljusgrå för bakgrunder */
--muted-foreground: 215 20% 45%; /* Mellangrå för mindre viktig text */
--muted-darker: 215 30% 30%;     /* Mörkare grå */
--muted-lighter: 220 10% 90%;    /* Ljusare grå */
--border: 220 14% 88%;           /* Border-färg */
```

### Kompletterande färger

**Grönt** - Success/Matrix-tema
- Terminal: `120 100% 50%`

**Rött** - Destructive/Error
- Destructive: `0 84.2% 60.2%`

---

## Layout & Spacing

### Konsekvent marginal på ALLA sidor

**CSS Custom Properties:**
```css
--page-padding-x: 1.5rem;  /* Vänster/höger marginal */
--page-padding-top: 2rem;  /* Topp-marginal */
```

**Utility Class:**
```css
.page-container {
  padding-left: var(--page-padding-x);
  padding-right: var(--page-padding-x);
  padding-top: var(--page-padding-top);
}
```

**REGEL:** Alla sidor ska använda `.page-container` eller motsvarande spacing för att undvika "hoppighet"

### Vänsterjustering

**REGEL:** Allt innehåll ska vara vänsterjusterat (ej centrerat) för konsistens.

---

## Header/Breadcrumb (KRITISKT)

**Använd ALLTID komponenten `<StandardBreadcrumb />`**

### Struktur (får INTE ändras)

1. **Terminal-ikon** `>_` - i ljusblått (`text-accent`)
2. **Home-länk** - Hus-ikon + "Home" text
   - Länkar till `/dashboard` (om inloggad) eller `/` (om ej inloggad)
3. **Breadcrumb-navigation** - Varje steg = klickbar länk
4. **Aktiv sida** (sista elementet) - **MÅSTE** vara i ljusblått (`text-accent`)

### Exempel på användning

```tsx
import { StandardBreadcrumb } from "@/components/StandardBreadcrumb";

// Enkel breadcrumb
<StandardBreadcrumb currentPage="Dashboard" />

// Med navigering
<StandardBreadcrumb
  items={[
    { label: "Domains", href: "/domains" },
    { label: "My Domain", href: "/domains/123" }
  ]}
  currentPage="Settings"
/>
```

**REGEL:** Samma breadcrumb-header på ALLA sidor - ingen variation!

---

## Komponenter & Visuella Element

### Kort (Cards)

```tsx
<Card className="border border-border bg-card">
  {/* Content */}
</Card>
```

- **Tunn ram** (`border`)
- **Vit bakgrund** (`bg-card`) mot ljusgrå body-bakgrund
- **Subtila skuggor** (`shadow-sm`, `shadow`)

### Skuggor

```css
--shadow-sm: 0 1px 2px 0 hsl(215 85% 9% / 0.05);
--shadow: 0 1px 3px 0 hsl(215 85% 9% / 0.1);
--shadow-lg: 0 10px 15px -3px hsl(215 85% 9% / 0.1);
```

Använd Tailwind-klasser: `shadow-sm`, `shadow`, `shadow-lg`

---

## Visuella Mönster

### Bakgrundsmönster

**Subtilt rutmönster** (på body som standard):
```css
background-image:
  linear-gradient(hsl(220 14% 88% / 0.3) 1px, transparent 1px),
  linear-gradient(90deg, hsl(220 14% 88% / 0.3) 1px, transparent 1px);
background-size: 20px 20px;
```

**Variationer** (för specifika sidor/sektioner):

```tsx
{/* Dots pattern */}
<div className="pattern-dots">...</div>

{/* Grid pattern (större rutnät) */}
<div className="pattern-grid">...</div>
```

**REGEL:** Använd subtila mönster slumpmässigt för visuell variation, men håll det diskret.

---

## Typografi

### Font

```css
font-family: 'JetBrains Mono', monospace;
```

**REGEL:** Använd `font-mono` på all text för terminal-känsla

### Textstorlekar

- Stora rubriker: `text-4xl` (36px)
- Medelstora rubriker: `text-2xl` (24px)
- Brödtext: `text-base` (16px) eller `text-sm` (14px)
- Mindre text: `text-xs` (12px)

---

## Interaktiva Element

### Länkar

```tsx
<a className="text-foreground hover:text-accent transition-colors">
  Link
</a>
```

- Normalt: `text-foreground`
- Hover: `text-accent`
- Aktiv sida i breadcrumb: `text-accent`

### Knappar

Använd befintliga button-varianter från `@/components/ui/button`

**Primär:**
```tsx
<Button variant="default">Action</Button>
```

**Sekundär:**
```tsx
<Button variant="outline">Action</Button>
```

---

## Implementering

### Steg för att följa designsystemet

1. **Importera StandardBreadcrumb** på alla sidor:
   ```tsx
   import { StandardBreadcrumb } from "@/components/StandardBreadcrumb";
   ```

2. **Använd page-container** för konsekvent spacing:
   ```tsx
   <div className="min-h-screen bg-background">
     <StandardBreadcrumb currentPage="My Page" />
     <main className="page-container">
       {/* Content */}
     </main>
   </div>
   ```

3. **Använd semantiska färger** från designsystemet:
   - `bg-background`, `bg-card`
   - `text-foreground`, `text-muted-foreground`, `text-accent`
   - `border-border`

4. **Lägg till subtila mönster** där det känns lämpligt:
   ```tsx
   <section className="pattern-dots p-8">
     {/* Content */}
   </section>
   ```

---

## Kontroll & Kvalitetssäkring

### Checklista för varje ny sida

- [ ] Använder `<StandardBreadcrumb />` med korrekt struktur
- [ ] Har konsekvent spacing via `.page-container` eller ekvivalent
- [ ] Använder endast semantiska färger från designsystemet (inga direkta färger)
- [ ] Vänsterjusterat innehåll
- [ ] Sista breadcrumb-elementet är i `text-accent`
- [ ] Kort använder `border-border` och `bg-card`
- [ ] Ingen direkt användning av `text-white`, `bg-white`, `text-black`, `bg-black` etc.

---

## Förbjudna Praktiker

❌ **Bryta breadcrumb-strukturen** - Terminal-ikon och home-länk MÅSTE alltid finnas
❌ **Använda direkta färger** - t.ex. `text-white`, `bg-blue-500` etc.
❌ **Olika spacing** på olika sidor - använd alltid `.page-container`
❌ **Centrerat innehåll** - allt ska vara vänsterjusterat
❌ **Hoppa över breadcrumb** - alla sidor MÅSTE ha den

---

## Framtida Tillägg

När nya komponenter eller patterns behöver läggas till:
1. Dokumentera här först
2. Följ befintliga färger och spacing
3. Testa konsistens med resten av siten
4. Uppdatera detta dokument

---

**Detta designsystem är levande och ska uppdateras vid behov, men kärnprinciperna (breadcrumb-struktur, spacing, färgpalett) får INTE ändras utan explicit godkännande.**
