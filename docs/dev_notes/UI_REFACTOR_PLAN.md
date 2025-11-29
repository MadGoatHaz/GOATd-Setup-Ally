# UI Refactor Plan: Apps Tab Overhaul

## Objective
Refactor the "Apps" tab in `src/apps.py` to use a **Tabbed Interface** for categories, a **Persistent Shopping Cart** for selected apps, and **Compact Buttons** to maximize screen real estate.

## 1. Widget Hierarchy Design

The new layout replaces the single `DataTable` with a `TabbedContent` container on the left and a split view on the right.

```mermaid
graph TD
    AppInstaller[AppInstaller (Horizontal)]
    
    LeftPanel[Left Panel (Vertical, 3fr)]
    RightPanel[Right Panel (Vertical, 1fr)]
    
    AppInstaller --> LeftPanel
    AppInstaller --> RightPanel
    
    LeftPanel --> Title[Title & Instructions]
    LeftPanel --> Tabs[TabbedContent]
    LeftPanel --> Actions[Action Buttons Row]
    
    Tabs --> Tab1[TabPane: Terminal]
    Tabs --> Tab2[TabPane: Creative]
    Tabs --> TabN[TabPane: ...]
    
    Tab1 --> Table1[DataTable]
    Tab2 --> Table2[DataTable]
    
    RightPanel --> CartSec[Cart Section (Vertical)]
    RightPanel --> LogSec[Log Section (Vertical)]
    
    CartSec --> CartLabel[Label: Selected Apps]
    CartSec --> CartList[ListView: self.selected_apps]
    
    LogSec --> LogLabel[Label: Installation Log]
    LogSec --> Log[RichLog]
```

## 2. Implementation Steps

### Step 1: State Management Refactor (`src/apps.py`)
The current implementation relies on the `DataTable` as the source of truth for selections. Since we are splitting the table into multiple tabs (and thus multiple tables), we must lift the state up to the `AppInstaller` class.

1.  Modify `AppInstaller.__init__`:
    -   Initialize `self.selected_apps = set()` to store package names (IDs).
2.  Create helper methods:
    -   `toggle_selection(pkg_id)`: Add/remove from set, then trigger UI updates.
    -   `update_cart_view()`: Refresh the Right Panel list based on `self.selected_apps`.

### Step 2: UI Layout Restructuring (`src/apps.py`)
Refactor the `compose()` method of `AppInstaller`.

1.  **Left Panel**:
    -   Replace the single `DataTable` with `TabbedContent`.
    -   Iterate through `APPS_CATEGORIES` (imported from top of file).
    -   For each category, yield a `TabPane(title=category)`.
    -   Inside each Pane, yield a unique `DataTable` (id=`table_{sanitized_category_name}`).
2.  **Right Panel**:
    -   Split into two sections (using `Vertical` containers or just stacking widgets).
    -   **Top**: "Cart" - A `ListView` or `Markdown` widget listing selected apps.
    -   **Bottom**: "Logs" - The existing `RichLog`.

### Step 3: Logic Updates (`src/apps.py`)
1.  **Populating Tables**:
    -   Update `refresh_app_status()` to loop through *all* created DataTables (query by class or ID pattern).
    -   When adding rows, check `pkg_id in self.selected_apps` to determine `[x]` vs `[ ]`.
2.  **Handling Events**:
    -   Update `on_cell_selected`:
        -   It must now handle events from *any* table.
        -   Instead of reading the cell value to toggle, check `self.selected_apps`.
        -   Update the cell in the specific table *and* update the Cart view.
3.  **Execution**:
    -   Update `install_selected()` and `uninstall_selected()` to read from `self.selected_apps` instead of scraping the table rows.

### Step 4: Button & Style Refactor (`src/styles.tcss`)
1.  Define a `.compact` CSS class in `src/styles.tcss`:
    -   Reduced `height` (e.g., `height: 1` or `height: auto`).
    -   Reduced `padding` (e.g., `0 1`).
    -   Smaller border or no border for a cleaner look.
2.  Apply `.compact` class to the buttons in `src/apps.py`.
3.  Style the new "Cart" list to look distinct (e.g., a border with a specific color).

## 3. Key Code Snippets

**Sanitizing Category Names for IDs:**
```python
def get_table_id(category):
    return f"table_{category.lower().replace(' ', '_').replace('&', '')}"
```

**Cart Update Logic:**
```python
def update_cart_view(self):
    cart_list = self.query_one("#cart_list", ListView)
    cart_list.clear()
    for pkg in self.selected_apps:
        cart_list.append(ListItem(Label(pkg)))