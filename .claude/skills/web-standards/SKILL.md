---
name: web-standards
description: Enforce web coding standards for pure HTML/CSS/JS development. Use this skill when building or reviewing any pure frontend project (HTML pages, landing pages, forms, dashboards). Ensures semantic HTML, BEM CSS, vanilla JS, and proper file separation with no frameworks or external dependencies.
license: Complete terms in LICENSE.txt
---

This skill defines mandatory coding standards for all pure HTML / CSS / JS frontend work. No frameworks, no build tools, no external CDN — only native browser capabilities. When invoked, **read every generated file against these rules before returning code to the user**.

## File Structure Rules

- **Minimum three files**: 1 `.html` + 1 `.css` + 1 `.js` per project/page
- **CSS** lives in `assets/css/` relative to the HTML file (e.g., `assets/css/style.css`)
- **JS** lives in `assets/js/` relative to the HTML file (e.g., `assets/js/main.js`)
- **Images/assets** live in `assets/img/` if needed
- **Never inline CSS or JS** inside the HTML file — no `<style>` blocks, no `<script>` without `src`, no `style=""` attributes
- **Link order**: CSS link(s) first in `<head>`, JS `<script src>` just before `</body>`
- Relative path references must use `../` correctly based on directory depth

```html
<!-- Correct link order -->
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="../assets/css/style.css">
    <title>Page Title</title>
</head>
<body>
    <!-- ... -->
    <script src="../assets/js/main.js"></script>
</body>
```

## HTML Standards

### Semantic Tags (Required)
Use semantic elements **instead of generic containers**:

| Instead Of | Use |
|---|---|
| `<div class="header">` | `<header>` |
| `<div class="nav">` | `<nav>` |
| `<div class="main-content">` | `<main>` |
| `<div class="section">` | `<section>` |
| `<div class="article">` | `<article>` |
| `<div class="footer">` | `<footer>` |
| `<div class="btn">` | `<button>` or `<a>` |

- **Non-div policy**: `<div>` and `<span>` are forbidden unless there is genuinely no semantic alternative (rare cases like layout wrappers that cannot be `<section>` or `<article>`)
- If a tag works, use it. A reviewer flagging `<div>` instead of `<header>` is correct behavior.

### Form Accessibility
- Every form input **must** have an associated `<label>` via `for`/`id` pairing
- Labels are **mandatory**, not optional

```html
<label for="email">邮箱地址</label>
<input type="email" id="email" name="email" required>
```

### Required Meta Tags
Every HTML file must include:

```html
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

### Other HTML Requirements
- Use `lang` attribute on `<html>` (e.g., `<html lang="zh-CN">`)
- Use `type="module"` in script tags when using ES modules
- Use `alt` text on all images
- Include `aria-label` or `aria-labelledby` where semantics alone don't convey purpose
- Use `rel="noopener noreferrer"` on external links with `target="_blank"`

## CSS Standards

### No External Dependencies
- **Zero frameworks allowed**: No Bootstrap, Tailwind, Bulma, Foundation, Materialize — nothing
- **Zero icon libraries**: No Font Awesome, Ionicons, Material Icons — use inline SVGs or CSS-only icons
- **No preprocessors**: No SASS/SCSS, Less, Stylus — write plain CSS
- **No CSS-in-JS libraries**: No styled-components, emotion, etc.

### CSS Custom Properties (Required)
Define color tokens and spacing as CSS variables at the root level:

```css
:root {
    --color-primary: #38bdf8;
    --color-text: #f8fafc;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 2rem;
}
```

Use variables consistently throughout stylesheets.

### Box-Sizing Reset (Required)
First rule in every stylesheet:

```css
*, *::before, *::after {
    box-sizing: border-box;
}
```

### BEM Naming Convention (Mandatory)
Follow Block__Element--Modifier structure:

```css
/* Block */
.card { ... }

/* Element */
.card__header { ... }
.card__body { ... }
.card__footer { ... }

/* Modifier */
.card--primary { ... }
.card__btn--active { ... }
```

- Blocks represent standalone components (`nav`, `card`, `form-group`, `login-btn`)
- Elements live inside blocks and cannot exist outside them
- Modifiers change appearance or state of blocks/elements
- Use double underscore `__` for elements, double hyphen `--` for modifiers

### CSS Quality Standards
- Avoid hardcoded magic numbers — prefer CSS variables for spacing and colors
- Media queries should use breakpoints stored in variables
- Support mobile-first responsive design
- Add comments for major sections (`/* ===== Header ===== */`)
- Keep specificity low — never chain more than 3 levels deep
- Use `transition` for interactive states, `animation` sparingly for meaningful effects

## JavaScript Standards

### No Frameworks
- **Zero libraries allowed**: No jQuery, React, Vue, Angular, Svelte — nothing
- **No build step**: No TypeScript compiler, Webpack, Vite — plain JS files served directly by the browser

### Modern Syntax (Required)
- Use `const` and `let` exclusively — **`var` is strictly forbidden**
- Prefer `const` by default, only use `let` when reassignment is necessary
- Use arrow functions for callbacks and short functions:
  ```javascript
  const handleClick = () => { ... };
  document.getElementById('submit').addEventListener('click', handleClick);
  ```
- Use async/await for asynchronous operations instead of raw Promise chains:
  ```javascript
  const fetchData = async () => {
      const response = await fetch('/api/data');
      return response.json();
  };
  ```

### Event Handling (Required)
- Always use `addEventListener` — **never use inline `onclick=""`**
- Store references to DOM elements in constants at module top
- Use event delegation when handling multiple similar items:
  ```javascript
  listContainer.addEventListener('click', (e) => {
      const item = e.target.closest('.list-item');
      if (!item) return;
      // handle click
  });
  ```

### DOM & Fetch Patterns
- Query DOM once at initialization, store in variables
- Use `document.querySelectorAll()` for multiple elements
- Use `fetch()` for HTTP requests with `async/await`:
  ```javascript
  const submitForm = async (formData) => {
      try {
          const response = await fetch('/api/login', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(formData)
          });
          return await response.json();
      } catch (error) {
          console.error('Request failed:', error);
          throw error;
      }
  };
  ```

### Other JS Standards
- Use template literals over string concatenation: `` `Hello ${name}` ``
- Use destructuring and spread/rest syntax appropriately
- Add error handling with try/catch for async operations
- Log helpful messages with `console.log`, `console.warn`, `console.error`
- Keep functions small and focused on a single responsibility

## Validation Checklist

Before returning any generated frontend code, verify every item:

- [ ] Three or more files exist (`.html` + `.css` + `.js`)
- [ ] No `<style>` blocks inside HTML — CSS in external file only
- [ ] No inline `<script>` in HTML — JS in external file only
- [ ] No inline `style=""` attributes anywhere
- [ ] Viewport meta tag present
- [ ] All visual containers use semantic tags (no unnecessary divs)
- [ ] All form inputs have associated labels
- [ ] CSS starts with `box-sizing: border-box` reset
- [ ] CSS uses custom properties for colors and spacing
- [ ] CSS follows BEM naming convention
- [ ] No framework imports (Bootstrap, Tailwind, etc.)
- [ ] No icon library imports (Font Awesome, etc.)
- [ ] JS uses `const`/`let` — zero `var` statements
- [ ] JS uses `addEventListener` — zero inline handlers
- [ ] JS uses `async/await` for async code

If any item fails, fix it before presenting the result to the user.
