---
allowed-tools: Bash(sspi metadata:*), Bash(sspi clean:*), Bash(sspi query:*), Bash(curl -s:*), Bash(git status:*) Bash(git diff:*), Bash(tree:*)
description: Edit the HTML, CSS, and JS on the webpage to achieve desired visuals and user-facing functionality (UX/UI)
---
You are working on a data visualization webpage written in HTML, CSS, and Javascript and powered by a Flask application.

CSS and Javascript for this project are bundled via @sspi_flask_app/assets.py. Bundle rebuilds must be triggered after every change by running `touch wsgi.py` in the current working directory.

## Bundled Files
- @sspi_flask_app/client/static/style.css
- @sspi_flask_app/client/static/script.js

## Unbundled Files
You will not be making changes to bundled files directly, but to the js and .css files that are used to compile them.

### CSS
The CSS for the page depends on a few key files:
1. @sspi_flask_app/client/static/css/variables.css : Defines key styles to be used. Always use colors and styles defined here when possible. Also defines Dark Mode / Light Mode styles, which you should respect in all of your CSS.
2. @sspi_flask_app/client/static/css/variables.css : Defines some base styles, which may affect how your CSS works later.

### Charts
All of the javascript for the charts lives in @sspi_flask_app/client/static/charts/

**File Tree**: 

!`tree sspi_flask_app/client/static/charts/`

**Plugins**: The charts depend on several plugins defined at @sspi_flask_app/client/static/charts/plugins.
**CSS**: The CSS for the charts can be found at @sspi_flask_app/client/static/css/charts/
**Panel Charts**: The main form of data we use for the SSPI is panel data, identified and the Country-Year level. As such, the fundamental chart type we use is a panel chart. We have several different flavors of panel chart, but all inherit from the PanelChart object found at @sspi_flask_app/client/static/charts/panel/panel-chart.js. Changes to the base class will affect all other charts, so be careful here and think hard about the inheritance patterns.

### Templating
Many routes rely on Jinja2 Templating to populate HTML pages with data.
