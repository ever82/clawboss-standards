# AI-Me Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interaction Layer                    │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   CLI Terminal  │   Claude Code   │   Install Scripts           │
└────────┬────────┴────────┬────────┴──────────────┬──────────────┘
         │                 │                       │
         └─────────────────┼───────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Application Service Layer (src/cli)            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ Command  │ │ Parameter│ │ Output   │ │ Interactive│           │
│  │ Parsing  │ │ Validation│ │ Formatting│ │ Prompts   │            │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘            │
└───────┼────────────┼────────────┼────────────┼────────────────────┘
        │            │            │            │
        └────────────┴──────┬─────┴────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Business Logic Layer (src/core)                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ Behavior     │ │ TreeService  │ │ Workspace    │             │
│  │ Service      │ │              │ │ Service      │             │
│  │              │ │              │ │              │             │
│  │ - create()   │ │ - buildTree()│ │ - create()   │             │
│  │ - update()   │ │ - move()     │ │ - open()     │             │
│  │ - delete()   │ │ - getPath()  │ │ - getFiles() │             │
│  │ - list()     │ │ - getDepth() │ │ - sync()     │             │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘             │
│         └────────────────┼────────────────┘                     │
│                          ▼                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ BehaviorClass│ │ ClassTree    │ │ ClassImport  │             │
│  │ Service      │ │ Service      │ │ / Export     │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
│                          │                                      │
│  ┌───────────────────────▼───────────────────────┐              │
│  │ StatusManager    │ ProgressCalc │ TagManager  │              │
│  └───────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Access Layer (src/db)                     │
│  ┌──────────────────────────────────────────────┐               │
│  │           Repository Pattern                 │               │
│  ┌────────────┐ ┌────────────┐ ┌──────────────┐ │               │
│  │ Behavior   │ │ BehaviorClass│ │ BehaviorTag │ │               │
│  │ Repository │ │ Repository │ │ Repository  │ │               │
│  └────────────┘ └────────────┘ └──────────────┘ │               │
│  └──────────────────────┬───────────────────────┘               │
│                         │                                       │
│  ┌──────────────────────▼───────────────────────┐               │
│  │         SQLite (better-sqlite3)              │               │
│  │     ~/ai-me/data/behaviors.db                │               │
│  └──────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    File System Layer                              │
│         ~/ai-me/workspaces/  (behavior workspaces)              │
│         ~/ai-me/classes/     (merged class documents)           │
│         ~/ai-me/data/        (database and backups)             │
│         ~/ai-me/.claude/     (Claude Code config)               │
└─────────────────────────────────────────────────────────────────┘
```

## Module Details

### 1. CLI Module (src/cli/)

**Responsibility**: Parse user input, call business logic, format output

```typescript
// Command registration example
program
  .command('create <name>')
  .option('-p, --parent <id>', 'Parent behavior ID')
  .option('-c, --class <id>', 'Behavior class ID')
  .option('--priority <level>', 'Priority')
  .action(async (name, options) => {
    const service = new BehaviorService();
    const behavior = await service.create({ name, ...options });
    console.log(`Created: ${behavior.id}`);
  });
```

### 2. Behavior Module (src/core/behavior.ts)

**Responsibility**: Behavior lifecycle management

```typescript
class BehaviorService {
  // Create behavior
  async create(input: CreateBehaviorInput): Promise<Behavior>

  // Update behavior (with status transition validation)
  async update(id: string, changes: UpdateBehaviorInput): Promise<Behavior>

  // Delete behavior (handle child behaviors)
  async delete(id: string, recursive: boolean): Promise<void>

  // Query behavior list
  async list(filter: BehaviorFilter): Promise<Behavior[]>

  // Get single behavior
  async get(id: string): Promise<Behavior | null>

  // Set active behavior (current context)
  async setActive(id: string): Promise<void>

  // Get current active behavior
  async getActive(): Promise<Behavior | null>

  // Check if behavior can start (all dependencies done)
  async canStart(id: string): Promise<{ canStart: boolean; blockingDeps: string[] }>

  // Get time report for behavior
  async getTimeReport(id: string): Promise<TimeReport>

  // **TRANSACTION MANAGEMENT**
  // All write operations ensure atomicity across multiple resources.
  // The following patterns are used:
  //
  // 1. **Database + File System Atomicity**:
  //    - create(): Database insert and workspace folder creation must both succeed or both fail.
  //    - Implementation uses two-phase commit:
  //      a) Insert to DB with status 'creating'
  //      b) Create workspace folder
  //      c) Update DB status to 'active'
  //      d) On failure: rollback by deleting DB record and cleaning up folder
  //
  // 2. **Database Transaction Boundaries**:
  //    - All repository operations within a single business operation share a transaction.
  //    - Example: create() wraps BehaviorRepository.create(), TagRepository.link(), and ActivityLogRepository.create() in one transaction.
  //
  // 3. **Compensating Transactions**:
  //    - For operations involving external resources (file system, git), implement compensating actions.
  //    - On failure, execute compensating actions to restore consistent state.
  //
  // 4. **Transaction Propagation**:
  //    - Service methods accept optional transaction context.
  //    - Nested service calls reuse the parent transaction (REQUIRED propagation).
  //
  // Example transaction handling:
  // ```typescript
  // async create(input: CreateBehaviorInput): Promise<Behavior> {
  //   const tx = await this.db.beginTransaction();
  //   try {
  //     // 1. Create database record
  //     const behavior = await this.behaviorRepo.create(input, tx);
  //
  //     // 2. Create workspace folder
  //     await this.workspaceService.create(behavior.id, tx);
  //
  //     // 3. Link tags if provided
   //     if (input.tags?.length) {
  //       await this.tagRepo.linkToBehavior(behavior.id, input.tags, tx);
  //     }
  //
  //     // 4. Log activity
  //     await this.activityRepo.create({ type: 'BEHAVIOR_CREATED', behaviorId: behavior.id }, tx);
  //
  //     await tx.commit();
  //     return behavior;
  //   } catch (error) {
  //     await tx.rollback();
  //     // Cleanup any created resources
  //     await this.compensateCreate(input);
  //     throw error;
  //   }
  // }
  // ```
}

interface CreateBehaviorInput {
  name: string;
  description?: string;
  parentId?: string;
  classId?: string;
  priority?: Priority;
  plannedDuration?: number;       // in minutes
  deadline?: Date;
  dependencies?: string[];        // behavior IDs
  acceptanceCriteria?: string[];  // descriptions
  tags?: string[];
}

interface UpdateBehaviorInput {
  name?: string;
  description?: string;
  status?: BehaviorStatus;
  priority?: Priority;
  parentId?: string;
  plannedDuration?: number;
  deadline?: Date;
  // Dependencies managed separately
  // Acceptance criteria managed separately
}

interface TimeReport {
  plannedDuration: number;        // minutes (user estimate)
  actualDuration: number;         // minutes (calculated)
  startTime?: Date;
  endTime?: Date;
  isRunning: boolean;
  timeSpentToday: number;         // minutes
  efficiency: number;             // actual / planned ratio
}
```

### 2.1 Dependency Module (src/core/dependency.ts)

**Responsibility**: Manage behavior dependencies

```typescript
class DependencyManager {
  // Add dependency (behaviorId depends on dependsOnId)
  async addDependency(behaviorId: string, dependsOnId: string): Promise<void>

  // Remove dependency
  async removeDependency(behaviorId: string, dependsOnId: string): Promise<void>

  // Get all dependencies of a behavior
  async getDependencies(behaviorId: string): Promise<Behavior[]>

  // Get all behaviors that depend on this behavior
  async getDependents(behaviorId: string): Promise<Behavior[]>

  // Check if a dependency would create a cycle
  wouldCreateCycle(behaviorId: string, dependsOnId: string): boolean

  // Get all blocking dependencies (not done)
  async getBlockingDependencies(behaviorId: string): Promise<Behavior[]>

  // Check if all dependencies are satisfied (all done)
  async areDependenciesSatisfied(behaviorId: string): Promise<boolean>
}

interface DependencyGraph {
  nodes: BehaviorNode[];
  edges: DependencyEdge[];
}

interface BehaviorNode {
  id: string;
  name: string;
  status: BehaviorStatus;
}

interface DependencyEdge {
  from: string;  // depends on
  to: string;    // this behavior
}
```

### 2.2 Criteria Module (src/core/criteria.ts)

**Responsibility**: Manage acceptance criteria

```typescript
class CriteriaManager {
  // Add acceptance criterion
  async addCriterion(behaviorId: string, description: string): Promise<Criterion>

  // Remove acceptance criterion
  async removeCriterion(behaviorId: string, criterionId: string): Promise<void>

  // Update criterion description
  async updateCriterion(behaviorId: string, criterionId: string, description: string): Promise<Criterion>

  // Mark criterion as completed
  async checkCriterion(behaviorId: string, criterionId: string): Promise<void>

  // Mark criterion as not completed
  async uncheckCriterion(behaviorId: string, criterionId: string): Promise<void>

  // Get all criteria for a behavior
  async getCriteria(behaviorId: string): Promise<Criterion[]>

  // Check if all criteria are completed
  async areAllCriteriaMet(behaviorId: string): Promise<boolean>

  // Get completion percentage
  async getCompletionPercentage(behaviorId: string): Promise<number>
}

interface Criterion {
  id: string;
  description: string;
  checked: boolean;
  checkedAt?: Date;
  createdAt: Date;
}
```

### 2.3 Timer Module (src/core/timer.ts)

**Responsibility**: Track time spent on behaviors

```typescript
class TimerManager {
  // Start timer for behavior (called when status -> doing)
  async start(behaviorId: string): Promise<void>

  // Stop timer for behavior (called when status -> paused/done)
  async stop(behaviorId: string): Promise<void>

  // Get current timer status
  async getStatus(behaviorId: string): Promise<TimerStatus>

  // Get accumulated duration
  async getDuration(behaviorId: string): Promise<number>  // in minutes

  // Reset timer (use with caution)
  async reset(behaviorId: string): Promise<void>
}

interface TimerStatus {
  isRunning: boolean;
  startTime?: Date;
  accumulatedDuration: number;  // minutes from previous sessions
  currentSessionDuration: number;  // minutes since last start
}
```

### 3.1 Time Aggregation Module (src/core/time-aggregator.ts)

**Responsibility**: Calculate total time (self + all descendants) for behaviors

```typescript
class TimeAggregator {
  // Calculate total time for a behavior (self + all descendants)
  async calculateTotalTime(behaviorId: string): Promise<TimeBreakdown>

  // Recalculate total time for a behavior and all its ancestors
  async updateAggregationChain(behaviorId: string): Promise<void>

  // Get detailed time breakdown for a behavior
  async getTimeBreakdown(behaviorId: string): Promise<TimeBreakdown>

  // Get time report for a behavior tree
  async getTreeTimeReport(rootId?: string): Promise<TreeTimeReport>

  // Calculate efficiency (actual / planned * 100)
  calculateEfficiency(actual: number, planned: number): number | null

  // Batch update all time aggregations (for maintenance)
  async recalculateAll(): Promise<RecalculationResult>

  // Check if aggregation needs update (based on cache timestamp)
  async needsRecalculation(behaviorId: string): Promise<boolean>

  // Get time statistics for system
  async getSystemTimeStats(options: StatsOptions): Promise<SystemTimeStats>
}

interface TimeBreakdown {
  behaviorId: string;
  behaviorName: string;

  // Self time (time spent directly on this behavior)
  self: {
    planned: number;          // minutes
    actual: number;           // minutes
    efficiency: number | null; // actual / planned * 100
  };

  // Children time (sum of all descendants)
  children: {
    planned: number;          // minutes
    actual: number;           // minutes
    efficiency: number | null;
    count: number;            // number of child behaviors
  };

  // Total time (self + children)
  total: {
    planned: number;          // minutes
    actual: number;           // minutes
    efficiency: number | null;
  };

  // Comparison
  variance: {
    planned: number;          // total.planned - self.planned
    actual: number;           // total.actual - self.actual
  };
}

interface TreeTimeReport {
  rootId: string;
  behaviors: TimeBreakdown[];
  summary: {
    totalBehaviors: number;
    totalPlanned: number;
    totalActual: number;
    overallEfficiency: number | null;
    overBudget: number;       // count of behaviors where actual > planned
    underBudget: number;      // count of behaviors where actual <= planned
  };
}

interface SystemTimeStats {
  totalBehaviors: number;
  totalCompleted: number;
  totalInProgress: number;

  // Time totals
  totalPlannedDuration: number;    // minutes
  totalActualDuration: number;     // minutes
  systemEfficiency: number | null; // actual / planned * 100

  // By status
  byStatus: Record<BehaviorStatus, {
    count: number;
    planned: number;
    actual: number;
  }>;

  // By behavior class
  byClass: Record<string, {
    className: string;
    count: number;
    avgEfficiency: number | null;
  }>;

  // Time periods
  byPeriod: Array<{
    period: string;          // e.g., "2024-03" or "2024-W12"
    planned: number;
    actual: number;
    completedCount: number;
  }>;
}
```

### 3.2 Tree Module (src/core/tree.ts)

**Responsibility**: Tree structure operations and navigation

```typescript
class TreeService {
  // Build tree structure
  buildTree(rootId?: string, depth?: number): BehaviorTreeNode

  // Get full path of behavior (from root to current)
  getPath(id: string): Behavior[]

  // Move behavior to new parent
  move(id: string, newParentId: string): Promise<void>

  // Get all descendants
  getDescendants(id: string): Behavior[]

  // Get direct children
  getChildren(id: string): Behavior[]

  // Calculate depth
  getDepth(id: string): number

  // Render as ASCII tree
  renderTree(rootId?: string): string
}

interface BehaviorTreeNode {
  behavior: Behavior;
  children: BehaviorTreeNode[];
  depth: number;
  isLast: boolean;
}
```

### 3.3 BehaviorClass Module (src/core/behavior-class.ts)

**Responsibility**: BehaviorClass CRUD and inheritance management

```typescript
class BehaviorClassService {
  // Create behavior class
  async create(input: CreateClassInput): Promise<BehaviorClass>

  // Update behavior class
  async update(id: string, changes: UpdateClassInput): Promise<BehaviorClass>

  // Delete behavior class (check if in use)
  async delete(id: string): Promise<void>

  // Get single behavior class
  async get(id: string): Promise<BehaviorClass | null>

  // List all behavior classes
  async list(): Promise<BehaviorClass[]>

  // Get inheritance chain (from root to current)
  async getInheritanceChain(id: string): Promise<BehaviorClass[]>

  // Get all subclasses
  async getSubClasses(id: string): Promise<BehaviorClass[]>

  // Merge inherited properties (rules, experiences, methods)
  async mergeInheritedDocs(id: string): Promise<MergedClassDocs>
}

interface BehaviorClass {
  id: string;                    // e.g., learning
  name: LocalizedText;           // Multi-language display names
  description: LocalizedText;    // Multi-language descriptions
  parentId: string | null;       // Parent class ID
  icon: string;                  // Emoji icon
  color: string;                 // Hex color
  source: 'system' | 'custom' | 'imported';
  author?: string;
  version: string;
  isSystem: boolean;
  isCustom: boolean;
  locales: string[];             // Supported locales
  createdAt: Date;
  updatedAt: Date;
}

interface LocalizedText {
  [locale: string]: string;      // { "en": "Learning", "zh": "学习" }
}

interface ClassDocument {
  id: number;
  classId: string;
  locale: string;                // e.g., "en", "zh", "ja"
  docPath: string;
  contentHash: string;
  createdAt: Date;
  updatedAt: Date;
}

interface MergedClassDocs {
  locale: string;
  rules: string[];
  experiences: string[];
  methods: Method[];
}

interface Method {
  name: string;
  description: string;
  steps: string[];
}
```

### 3.4 ClassTree Module (src/core/class-tree.ts)

**Responsibility**: Behavior class inheritance tree management

```typescript
class ClassTreeService {
  // Build class inheritance tree
  buildClassTree(rootId?: string): ClassTreeNode

  // Check if can inherit (prevent circular inheritance)
  canInherit(childId: string, parentId: string): boolean

  // Get class inheritance path
  getInheritancePath(id: string): BehaviorClass[]

  // Render class tree as ASCII
  renderClassTree(): string

  // Find recommended subclasses
  findRecommendedSubClasses(parentClassId: string): BehaviorClass[]
}

interface ClassTreeNode {
  class: BehaviorClass;
  children: ClassTreeNode[];
  depth: number;
}
```

### 3.5 ClassTreeImporter Module (src/core/class-importer.ts)

**Responsibility**: Import behavior classes from directory tree to database

```typescript
class ClassTreeImporter {
  // Import from directory
  async importFromDirectory(dirPath: string, options: ImportOptions): Promise<ImportResult>

  // Import from official repository
  async importFromOfficial(options: ImportOptions): Promise<ImportResult>

  // Import from GitHub
  async importFromGitHub(repoUrl: string, options: ImportOptions): Promise<ImportResult>

  // Preview changes (dry-run)
  async previewImport(dirPath: string): Promise<ImportPreview>

  // Parse directory structure
  private parseDirectoryTree(dirPath: string): ParsedClassNode[]

  // Read and validate _class.yaml
  private readClassYaml(yamlPath: string): ClassYamlDefinition

  // Read _doc.md
  private readClassDoc(docPath: string): ClassDocContent

  // Build inheritance relationships
  private buildInheritance(tree: ParsedClassNode[]): ClassWithParent[]
}

interface ImportOptions {
  merge?: boolean;        // true=merge, false=overwrite (default)
  dryRun?: boolean;       // Preview only, no execution
  includeDocs?: boolean;  // Whether to import documents
}

interface ImportResult {
  imported: number;       // Number of imported classes
  updated: number;        // Number of updated classes
  skipped: number;        // Number of skipped classes
  errors: ImportError[];  // Error list
}

interface ParsedClassNode {
  path: string;           // Directory path
  depth: number;          // Depth
  classDef: ClassYamlDefinition;
  docContent?: ClassDocContent;
  parentPath?: string;    // Parent directory path
}
```

### 3.6 ClassTreeExporter Module (src/core/class-exporter.ts)

**Responsibility**: Export behavior classes from database to directory tree

```typescript
class ClassTreeExporter {
  // Export to directory
  async exportToDirectory(dirPath: string, options: ExportOptions): Promise<ExportResult>

  // Package as zip
  async exportToPackage(packagePath: string, options: ExportOptions): Promise<void>

  // Generate _index.yaml
  private generateIndexYaml(classes: BehaviorClass[]): IndexYamlContent

  // Generate _class.yaml
  private generateClassYaml(classData: BehaviorClass): ClassYamlContent

  // Generate _doc.md
  private generateClassDoc(classData: BehaviorClass): string
}

interface ExportOptions {
  includeSystem?: boolean;  // Whether to include system classes
  author?: string;          // Author name
  version?: string;         // Version number
  onlyCustom?: boolean;     // Only export user custom classes
}

interface ExportResult {
  exported: number;         // Number of exported classes
  path: string;             // Export directory path
}
```

### 3.7 Workspace Module (src/core/workspace.ts)

**Responsibility**: Workspace folder management

```typescript
class WorkspaceService {
  // Create workspace
  create(behaviorId: string, parentPath?: string): Promise<string>

  // Open workspace (in file manager)
  open(behaviorId: string): Promise<void>

  // Get workspace path
  getPath(behaviorId: string): string

  // Sync behavior tree structure to folder structure
  syncStructure(): Promise<void>

  // Cleanup orphaned workspace folders
  cleanup(): Promise<void>

  // List files in workspace
  listFiles(behaviorId: string): WorkspaceFile[]
}
```

### 3.8 Status Module (src/core/status.ts)

**Responsibility**: Status management and transitions

```typescript
enum BehaviorStatus {
  TODO = 'todo',
  DOING = 'doing',
  DONE = 'done',
  PAUSED = 'paused',
  BLOCKED = 'blocked'
}

class StatusManager {
  // Validate if status transition is legal
  canTransition(from: BehaviorStatus, to: BehaviorStatus): boolean

  // Auto-calculate parent behavior progress
  calculateProgress(behaviorId: string): number

  // Events triggered on status transition
  onTransition(behaviorId: string, from: BehaviorStatus, to: BehaviorStatus): void
}

// Status transition graph
const validTransitions: Record<BehaviorStatus, BehaviorStatus[]> = {
  [BehaviorStatus.TODO]: [BehaviorStatus.DOING, BehaviorStatus.PAUSED],
  [BehaviorStatus.DOING]: [BehaviorStatus.DONE, BehaviorStatus.PAUSED, BehaviorStatus.BLOCKED],
  [BehaviorStatus.DONE]: [BehaviorStatus.DOING],
  [BehaviorStatus.PAUSED]: [BehaviorStatus.TODO, BehaviorStatus.DOING],
  [BehaviorStatus.BLOCKED]: [BehaviorStatus.DOING, BehaviorStatus.PAUSED]
};
```

### 3.9 i18n Module (src/utils/i18n.ts)

**Responsibility**: Internationalization and localization

```typescript
class I18nManager {
  private currentLocale: string;
  private supportedLocales: string[];
  private fallbackLocale: string = 'en';

  constructor() {
    this.currentLocale = this.loadUserLocale();
    this.supportedLocales = ['en', 'zh'];  // Currently supports English and Chinese
  }

  // Get current locale
  getCurrentLocale(): string

  // Set locale and persist to config
  setLocale(locale: string): void

  // Get localized text from multi-language object
  t(localizedText: LocalizedText, locale?: string): string

  // Get localized class name
  getClassName(classData: BehaviorClass, locale?: string): string

  // Get localized class description
  getClassDescription(classData: BehaviorClass, locale?: string): string

  // Get document path for specific locale
  getLocalizedDocPath(classId: string, locale?: string): string

  // Find best available locale
  findBestLocale(availableLocales: string[], preferred?: string): string

  // Load user locale from config
  private loadUserLocale(): string

  // Save user locale to config
  private saveUserLocale(locale: string): void
}

// Usage examples:
// i18n.t({ en: "Learning", zh: "学习" }) -> "Learning" or "学习"
// i18n.getClassName(classData) -> Localized class name
```

### 3.10 AI Integration Module (src/ai/)

**Natural Language Parsing**: Simple keyword matching + intent recognition

```typescript
class NaturalLanguageParser {
  parse(input: string): ParsedIntent {
    // Recognize intent type
    if (this.matchesCreate(input)) {
      return { type: 'CREATE', data: this.extractCreateData(input) };
    }
    if (this.matchesCreateWithClass(input)) {
      return { type: 'CREATE_WITH_CLASS', data: this.extractCreateWithClassData(input) };
    }
    if (this.matchesUpdate(input)) {
      return { type: 'UPDATE', data: this.extractUpdateData(input) };
    }
    if (this.matchesQuery(input)) {
      return { type: 'QUERY', data: this.extractQueryData(input) };
    }
    if (this.matchesClassQuery(input)) {
      return { type: 'CLASS_QUERY', data: this.extractClassQueryData(input) };
    }
    return { type: 'UNKNOWN' };
  }
}
```

### 3.11 Database Module (src/db/)

**Repository Pattern**

```typescript
abstract class BaseRepository<T> {
  protected db: Database;

  constructor(db: Database) {
    this.db = db;
  }

  abstract findById(id: string): T | null;
  abstract findAll(filter?: Filter): T[];
  abstract create(data: CreateInput<T>): T;
  abstract update(id: string, data: UpdateInput<T>): T;
  abstract delete(id: string): void;
}

class BehaviorRepository extends BaseRepository<Behavior> {
  // Behavior-specific query methods - only generic CRUD and basic queries
  findByParentId(parentId: string | null): Behavior[]
  findByStatus(status: BehaviorStatus): Behavior[]
  findByTag(tagId: string): Behavior[]
  findByClass(classId: string): Behavior[]
  findActive(): Behavior | null
  setActive(id: string): void
  updateProgress(id: string, progress: number): void

  // Generic filter-based query - Repository provides data access only
  // Business logic queries (findOverdue, findDueSoon) moved to BehaviorService
  findByFilter(filter: BehaviorFilter): Behavior[]

  // Time aggregation queries - Repository provides data access only
  findTimeOverrun(): Behavior[]                               // simple field comparison
  findWithTimeData(): Behavior[]                              // behaviors with time tracking
  getTimeStatsByStatus(): Record<BehaviorStatus, TimeStats>  // stats grouped by status
  getTimeStatsByClass(): Record<string, TimeStats>           // stats grouped by behavior class

  // Dependency queries - basic lookups
  findByDependency(dependsOnId: string): Behavior[]           // behaviors depending on this
  findWithUnsatisfiedDeps(): Behavior[]                       // blocked by dependencies

  // Update time aggregation - data access only
  updateTimeAggregation(id: string, data: TimeAggregationData): void
  markAggregationDirty(id: string): void                      // mark for recalculation
  findDirtyAggregations(): Behavior[]                         // find behaviors needing recalculation
}

// Business logic queries moved to BehaviorService
class BehaviorService {
  // Repository instance for data access
  private behaviorRepo: BehaviorRepository;

  // Time-related business queries (moved from Repository)
  async findOverdue(): Promise<Behavior[]> {
    const now = new Date();
    return this.behaviorRepo.findByFilter({
      dueBefore: now,
      status: ['todo', 'doing', 'paused', 'blocked']  // exclude done
    });
  }

  async findDueSoon(days: number): Promise<Behavior[]> {
    const now = new Date();
    const future = new Date(now.getTime() + days * 24 * 60 * 60 * 1000);
    return this.behaviorRepo.findByFilter({
      dueAfter: now,
      dueBefore: future
    });
  }

  async findByTimeRange(start: Date, end: Date): Promise<Behavior[]> {
    return this.behaviorRepo.findByFilter({
      dueAfter: start,
      dueBefore: end
    });
  }

  async findByEfficiency(min?: number, max?: number): Promise<Behavior[]> {
    return this.behaviorRepo.findByFilter({
      efficiencyMin: min,
      efficiencyMax: max
    });
  }
}

interface TimeAggregationData {
  selfPlannedDuration: number;
  selfActualDuration: number;
  totalPlannedDuration: number;
  totalActualDuration: number;
  timeEfficiency: number | null;
  childrenTimeCachedAt: Date;
}

interface TimeStats {
  count: number;
  totalPlanned: number;    // minutes
  totalActual: number;     // minutes
  avgEfficiency: number | null;
}

class DependencyRepository {
  // Get all dependencies for a behavior
  findByBehaviorId(behaviorId: string): string[]              // returns depends_on_id array

  // Add dependency
  addDependency(behaviorId: string, dependsOnId: string): void

  // Remove dependency
  removeDependency(behaviorId: string, dependsOnId: string): void

  // Check if dependency exists
  exists(behaviorId: string, dependsOnId: string): boolean

  // Get dependency graph
  getDependencyGraph(rootId: string): DependencyGraph

  // Check for circular dependency
  wouldCreateCycle(behaviorId: string, dependsOnId: string): boolean
}

class CriteriaRepository {
  // Get all criteria for a behavior
  findByBehaviorId(behaviorId: string): Criterion[]

  // Get single criterion
  findById(criterionId: string): Criterion | null

  // Create criterion
  create(behaviorId: string, description: string): Criterion

  // Update criterion
  update(criterionId: string, data: Partial<Criterion>): Criterion

  // Delete criterion
  delete(criterionId: string): void

  // Toggle checked status
  toggleChecked(criterionId: string): void

  // Get completion stats
  getCompletionStats(behaviorId: string): { total: number; checked: number }
}

interface Behavior {
  id: string;
  name: string;
  description: string;
  status: BehaviorStatus;
  parentId: string | null;
  classId: string | null;
  workspacePath: string;
  priority: Priority;

  // Time management - SELF (direct time on this behavior)
  selfPlannedDuration: number;       // minutes, user estimate for this behavior only
  selfActualDuration: number;        // minutes, actual time spent on this behavior only
  startTime?: Date;                  // when first started
  endTime?: Date;                    // when completed
  deadline?: Date;                   // target completion

  // Time management - TOTAL (self + all descendants, auto-calculated)
  totalPlannedDuration: number;      // minutes, including all children
  totalActualDuration: number;       // minutes, including all children
  timeEfficiency: number | null;     // total_actual / total_planned * 100
  childrenTimeCachedAt?: Date;       // when aggregation was last calculated

  // Progress
  progress: number;                  // 0-100

  // Metadata
  createdAt: Date;
  updatedAt: Date;
  tags: string[];
}

interface BehaviorFilter {
  status?: BehaviorStatus | BehaviorStatus[];  // Single status or array of statuses
  priority?: Priority | Priority[];            // Single priority or array
  parentId?: string | null;
  classId?: string;
  tagId?: string;
  overdue?: boolean;                 // filter overdue behaviors
  blocked?: boolean;                 // filter blocked by dependencies
  dueBefore?: Date;                  // filter by deadline
  dueAfter?: Date;                   // filter by deadline
  efficiencyMin?: number;            // filter by efficiency >= N%
  efficiencyMax?: number;            // filter by efficiency <= N%
  timeOverrun?: boolean;             // filter where actual > planned
}
  // BehaviorClass-specific query methods
  findByParentId(parentId: string | null): BehaviorClass[]
  findRoots(): BehaviorClass[] // Find root classes (no parent)
  findSubClasses(classId: string): BehaviorClass[]
  isInUse(classId: string): boolean // Check if any behavior uses this class
  getInheritanceChain(classId: string): BehaviorClass[] // Get inheritance chain
}
```

## Layered Architecture with Validation

### Architecture Layers Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: User Interface (CLI / API / Web)                   │
│ - Command parsing                                           │
│ - Display formatting                                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Validation Layer (src/validation/)                 │
│ - Input validation and sanitization                         │
│ - Schema validation                                         │
│ - Business rule pre-checks                                  │
│ - Error message localization                                │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Application Service (src/cli, src/api)             │
│ - Request handling                                          │
│ - Transaction coordination                                  │
│ - Cross-cutting concerns (logging, metrics)                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Business Logic (src/core)                          │
│ - Domain entities                                           │
│ - Business rules and workflows                              │
│ - State management                                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: Data Access (src/db)                               │
│ - Repository pattern                                        │
│ - Query builders                                            │
│ - Connection management                                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 6: Infrastructure (SQLite, File System)               │
│ - Database                                                  │
│ - File storage                                              │
│ - External services                                         │
└─────────────────────────────────────────────────────────────┘
```

### Validation Layer (src/validation/)

**Responsibility**: Centralized input validation and sanitization, decoupled from business logic.

```typescript
// Validation layer - validates inputs before they reach business logic
class ValidationService {
  // Validate behavior creation input
  validateCreateBehavior(input: CreateBehaviorInput): ValidationResult<CreateBehaviorInput>

  // Validate behavior update input
  validateUpdateBehavior(input: UpdateBehaviorInput): ValidationResult<UpdateBehaviorInput>

  // Validate class creation
  validateCreateClass(input: CreateClassInput): ValidationResult<CreateClassInput>

  // Generic schema validation
  validate<T>(data: unknown, schema: ValidationSchema<T>): ValidationResult<T>

  // Sanitize user input (prevent injection)
  sanitizeString(input: string): string

  // Validate date ranges
  validateDateRange(start: Date, end: Date): ValidationResult<{ start: Date; end: Date }>

  // Validate behavior filter
  validateBehaviorFilter(filter: BehaviorFilter): ValidationResult<BehaviorFilter>
}

interface ValidationResult<T> {
  valid: boolean;
  data?: T;           // Sanitized/transformed data
  errors: ValidationError[];
}

interface ValidationError {
  field: string;
  code: ValidationErrorCode;
  message: LocalizedText;
}

enum ValidationErrorCode {
  REQUIRED = 'REQUIRED',
  INVALID_FORMAT = 'INVALID_FORMAT',
  INVALID_TYPE = 'INVALID_TYPE',
  INVALID_RANGE = 'INVALID_RANGE',
  INVALID_DATE = 'INVALID_DATE',
  STRING_TOO_LONG = 'STRING_TOO_LONG',
  STRING_TOO_SHORT = 'STRING_TOO_SHORT',
  INVALID_ENUM = 'INVALID_ENUM',
  PATTERN_MISMATCH = 'PATTERN_MISMATCH',
  CIRCULAR_REFERENCE = 'CIRCULAR_REFERENCE'
}

// Schema definition helpers
const BehaviorSchemas = {
  createBehavior: {
    name: { required: true, minLength: 1, maxLength: 200, sanitize: true },
    description: { required: false, maxLength: 5000, sanitize: true },
    plannedDuration: { required: false, min: 1, max: 10080 }, // max 1 week in minutes
    deadline: { required: false, future: true },
    priority: { required: false, enum: ['low', 'medium', 'high', 'urgent'] },
    parentId: { required: false, pattern: /^[a-z0-9-]+$/ },
    classId: { required: false, pattern: /^[a-z0-9-]+$/ },
    tags: { required: false, maxItems: 10, itemValidator: validateTag }
  },

  updateBehavior: {
    name: { required: false, minLength: 1, maxLength: 200, sanitize: true },
    status: { required: false, enum: ['todo', 'doing', 'done', 'paused', 'blocked'] },
    // ... other fields
  }
};
```

### Validation in Service Layer

Service layer delegates validation to ValidationService before processing:

```typescript
class BehaviorService {
  private validator: ValidationService;
  private behaviorRepo: BehaviorRepository;

  async create(input: CreateBehaviorInput): Promise<Behavior> {
    // Step 1: Validate input (Validation Layer)
    const validation = this.validator.validateCreateBehavior(input);
    if (!validation.valid) {
      throw new ValidationError(validation.errors);
    }

    // Step 2: Business rule validation (Business Logic Layer)
    if (input.parentId) {
      const parent = await this.behaviorRepo.findById(input.parentId);
      if (!parent) {
        throw new AIMeError(ErrorCode.BEHAVIOR_NOT_FOUND, 'Parent not found');
      }
      // Check depth limit
      const depth = await this.calculateDepth(input.parentId);
      if (depth >= MAX_TREE_DEPTH) {
        throw new AIMeError(ErrorCode.TREE_TOO_DEEP, `Maximum tree depth (${MAX_TREE_DEPTH}) exceeded`);
      }
    }

    // Step 3: Proceed with creation
    // ...
  }
}
```

### Benefits of Validation Layer

1. **Separation of Concerns**: Validation logic is isolated from business logic
2. **Reusability**: Same validators can be used by CLI, API, and batch imports
3. **Consistency**: All inputs validated against same rules
4. **Security**: Centralized sanitization prevents injection attacks
5. **Testability**: Validation rules can be tested independently
6. **Maintainability**: Changes to validation rules don't affect business logic

### Create Behavior Flow

```
User Input → CLI Parsing → BehaviorService.create()
                              │
                              ▼
                    ┌─────────────────────┐
                    │   1. Generate ID    │
                    │   2. Link Class     │ ← Optional: specify class_id
                    │   3. Create Workspace│
                    │   4. Save to DB     │
                    │   5. Update Parent  │
                    └─────────────────────┘
                              │
                              ▼
                    Return Behavior → CLI Display
```

### Create BehaviorClass Flow

```
User Input → CLI Parsing → BehaviorClassService.create()
                              │
                              ▼
                    ┌─────────────────────┐
                    │   1. Generate ID    │
                    │   2. Validate Parent│ ← If parent_id provided
                    │   3. Create Doc Template│ ← From templates/class-doc/
                    │   4. Save to DB     │
                    │   5. Open Editor    │ ← Optional
                    └─────────────────────┘
                              │
                              ▼
                    Return Class → CLI Display
```

### Import Class Tree Flow

```
User Input → CLI Parsing → ClassTreeImporter.importFromDirectory()
                              │
                              ▼
                    ┌─────────────────────┐
                    │   1. Scan Directory │
                    │   2. Parse YAML     │
                    │   3. Validate       │
                    │   4. Build Tree     │
                    │   5. Save to DB     │
                    └─────────────────────┘
                              │
                              ▼
                    Return Result → CLI Display
```

### Status Update Flow

```
User Input → CLI Parsing → BehaviorService.updateStatus()
                              │
                              ▼
                    ┌─────────────────────┐
                    │  Check Dependencies │ ← If transitioning to "doing"
                    │  - Get all deps     │
                    │  - Check if all done│
                    └─────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │ All dependencies satisfied      │ Has blocking dependencies
              ▼                               ▼
    ┌─────────────────────┐          Return Error with
    │  Check Acceptance   │          blocking behavior IDs
    │  Criteria (if       │
    │  marking as done)   │
    └─────────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │  StatusManager      │
    │  - Validate flow    │
    │  - Execute update   │
    └─────────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │  TimerManager       │
    │  - todo→doing:      │
    │    start timer      │
    │  - doing→done:      │
    │    stop timer,      │
    │    calc duration    │
    └─────────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │  TimeAggregator     │ ← NEW: Update time aggregation
    │  - Update self_     │    for this behavior
    │    actual_duration  │
    │  - Recalculate      │
    │    total_actual for │
    │    all ancestors    │
    └─────────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │  If marking done    │
    │  - Set end_time     │
    │  - Calc efficiency  │
    │  - Recalc parent    │
    │    progress         │
    └─────────────────────┘
```

### Time Aggregation Update Flow

**Performance Risk**: "Update all ancestors" strategy is inefficient for deep trees.

**Optimization Strategies**:
1. Lazy Evaluation: Mark ancestors as dirty, recalculate on demand
2. Optimistic Locking: Add version numbers for concurrent updates
3. Batch Updates: Queue updates and process in batches
4. Event-driven: Use event queue for async updates

```typescript
// Optimized Time Aggregation Update Flow with Lazy Evaluation

interface BehaviorTimeData {
  id: string;
  selfPlannedDuration: number;
  selfActualDuration: number;
  totalPlannedDuration: number;  // Cached total
  totalActualDuration: number;   // Cached total
  timeEfficiency: number | null;
  aggregationVersion: number;     // Optimistic locking version
  aggregationDirty: boolean;      // Lazy evaluation flag
  aggregationDirtyAt: Date | null;
}

class TimeAggregatorOptimized {
  private updateQueue: Set<string> = new Set();
  private batchTimer: NodeJS.Timeout | null = null;
  private readonly BATCH_DELAY = 100; // ms

  // On timer stop - mark ancestors dirty instead of immediate update
  async onTimerStop(behaviorId: string): Promise<void> {
    // Update self time
    await this.updateSelfTime(behaviorId);

    // Mark this behavior as needing recalculation
    await this.markDirty(behaviorId);

    // Queue ancestors for batch update (don't update immediately)
    const ancestors = await this.getAncestors(behaviorId);
    for (const ancestorId of ancestors) {
      this.updateQueue.add(ancestorId);
    }

    // Schedule batch processing
    this.scheduleBatchUpdate();
  }

  // Lazy evaluation: get time data, recalculate if dirty
  async getTimeData(behaviorId: string): Promise<TimeBreakdown> {
    const behavior = await this.behaviorRepo.findById(behaviorId);

    // If dirty, recalculate before returning
    if (behavior.aggregationDirty) {
      return await this.recalculateAndCache(behaviorId);
    }

    // Return cached data
    return this.toTimeBreakdown(behavior);
  }

  // Optimistic locking update
  async recalculateAndCache(behaviorId: string): Promise<TimeBreakdown> {
    const behavior = await this.behaviorRepo.findById(behaviorId);
    const currentVersion = behavior.aggregationVersion;

    // Calculate new totals
    const timeBreakdown = await this.calculateTimeBreakdown(behaviorId);

    try {
      // Update with version check
      await this.behaviorRepo.updateTimeAggregation(behaviorId, {
        totalPlannedDuration: timeBreakdown.total.planned,
        totalActualDuration: timeBreakdown.total.actual,
        timeEfficiency: timeBreakdown.total.efficiency,
        aggregationVersion: currentVersion + 1,
        aggregationDirty: false
      });
    } catch (error) {
      // Version conflict detected - another process updated
      if (error.code === 'VERSION_CONFLICT') {
        // Retry with fresh data
        return await this.recalculateAndCache(behaviorId);
      }
      throw error;
    }

    return timeBreakdown;
  }

  // Batch process queued updates
  private scheduleBatchUpdate(): void {
    if (this.batchTimer) return;

    this.batchTimer = setTimeout(async () => {
      await this.processBatch();
      this.batchTimer = null;
    }, this.BATCH_DELAY);
  }

  private async processBatch(): Promise<void> {
    const ids = Array.from(this.updateQueue);
    this.updateQueue.clear();

    // Process in order from leaves to root
    const sortedIds = await this.topologicalSort(ids);

    for (const id of sortedIds) {
      await this.markDirty(id);
    }
  }
}

// Original Flow (for comparison):
//
// Behavior timer stops
//         │
//         ▼
// ┌─────────────────────┐
// │ BehaviorService     │
// │ - Update self_      │
// │   actual_duration   │
// │   (add session      │
// │   duration)         │
// └─────────────────────┘
//         │
//         ▼
// ┌─────────────────────┐
// │ TimeAggregator      │
// │ - Get this behavior │
// │ - Get all children  │
// │ - Recalculate       │
// │   total_actual:     │
// │   self + sum(children)
// │ - Calculate         │
// │   efficiency        │
// └─────────────────────┘
//         │
//         ▼
// ┌─────────────────────┐
// │ Update all          │
// │ ancestors           │
// │ (walk up parent     │
// │ chain)              │
// └─────────────────────┘
//         │
//         ▼
// ┌─────────────────────┐
// │ For each ancestor:  │
// │ - Recalc its total  │
// │ - Update DB         │
// │ - Cache timestamp   │
// └─────────────────────┘
//         │
//         ▼
// Done - all totals updated
```

### Time Aggregation Calculation

**Risk**: Recursive calculation can cause stack overflow on deeply nested trees.

**Mitigation Strategy**:
1. Recursion depth limit (max 5 levels) - enforced at runtime
2. Iterative alternative using explicit stack
3. Database CHECK constraint to prevent circular parent references

```typescript
// Database constraint to prevent circular references
// ALTER TABLE behaviors ADD CONSTRAINT check_no_circular_parent
// CHECK (id != parent_id AND depth <= 5);

// Configuration
const MAX_TREE_DEPTH = 5;

// Iterative version using explicit stack (preferred for production)
function calculateTotalTimeIterative(behaviorId: string): TimeBreakdown {
  const visited = new Set<string>();  // Track visited nodes to detect cycles
  const stack: Array<{ id: string; depth: number }> = [{ id: behaviorId, depth: 0 }];
  const results = new Map<string, TimeBreakdown>();

  while (stack.length > 0) {
    const { id, depth } = stack.pop()!;

    // Safety checks
    if (depth > MAX_TREE_DEPTH) {
      throw new AIMeError(
        ErrorCode.TREE_TOO_DEEP,
        `Tree depth exceeds maximum limit of ${MAX_TREE_DEPTH}`,
        { behaviorId: id, depth }
      );
    }

    if (visited.has(id)) {
      throw new AIMeError(
        ErrorCode.CIRCULAR_DEPENDENCY,
        `Circular dependency detected in tree`,
        { behaviorId: id }
      );
    }
    visited.add(id);

    const behavior = getBehavior(id);
    if (!behavior) continue;

    // Get children for processing
    const children = getChildren(id);

    // If children not yet calculated, push back and process children first
    const unprocessedChildren = children.filter(child => !results.has(child.id));
    if (unprocessedChildren.length > 0) {
      stack.push({ id, depth });  // Re-process after children
      for (const child of unprocessedChildren) {
        stack.push({ id: child.id, depth: depth + 1 });
      }
      continue;
    }

    // Calculate totals
    let childrenActual = 0;
    let childrenPlanned = 0;

    for (const child of children) {
      const childTime = results.get(child.id)!;
      childrenActual += childTime.total.actual;
      childrenPlanned += childTime.total.planned;
    }

    const selfActual = behavior.self_actual_duration;
    const selfPlanned = behavior.self_planned_duration;
    const totalActual = selfActual + childrenActual;
    const totalPlanned = selfPlanned + childrenPlanned;

    results.set(id, {
      self: { planned: selfPlanned, actual: selfActual, efficiency: calculateEff(selfActual, selfPlanned) },
      children: { planned: childrenPlanned, actual: childrenActual, count: children.length },
      total: { planned: totalPlanned, actual: totalActual, efficiency: calculateEff(totalActual, totalPlanned) }
    });
  }

  return results.get(behaviorId)!;
}

// Recursive version with depth safety (for reference only)
function calculateTotalTime(behaviorId: string, depth: number = 0): TimeBreakdown {
  // Safety check: prevent stack overflow
  if (depth > MAX_TREE_DEPTH) {
    throw new AIMeError(
      ErrorCode.TREE_TOO_DEEP,
      `Tree depth exceeds maximum limit of ${MAX_TREE_DEPTH}`,
      { behaviorId, depth }
    );
  }

  const behavior = getBehavior(behaviorId);

  // Get self time
  const selfActual = behavior.self_actual_duration;
  const selfPlanned = behavior.self_planned_duration;

  // Get children
  const children = getChildren(behaviorId);

  // Calculate children totals with depth tracking
  let childrenActual = 0;
  let childrenPlanned = 0;

  for (const child of children) {
    const childTime = calculateTotalTime(child.id, depth + 1);  // Increment depth
    childrenActual += childTime.total.actual;
    childrenPlanned += childTime.total.planned;
  }

  // Calculate totals
  const totalActual = selfActual + childrenActual;
  const totalPlanned = selfPlanned + childrenPlanned;

  // Calculate efficiency
  const selfEfficiency = selfPlanned > 0
    ? (selfActual / selfPlanned) * 100
    : null;
  const totalEfficiency = totalPlanned > 0
    ? (totalActual / totalPlanned) * 100
    : null;

  return {
    self: { planned: selfPlanned, actual: selfActual, efficiency: selfEfficiency },
    children: { planned: childrenPlanned, actual: childrenActual, count: children.length },
    total: { planned: totalPlanned, actual: totalActual, efficiency: totalEfficiency }
  };
}

function calculateEff(actual: number, planned: number): number | null {
  return planned > 0 ? (actual / planned) * 100 : null;
}
```

### Dependency Check Flow

```
User tries to start behavior
              │
              ▼
    ┌─────────────────────┐
    │  DependencyManager  │
    │  - Get all deps     │
    │  - Check each status│
    └─────────────────────┘
              │
              ▼
              │
    ┌─────────┴─────────┐
    │ All done          │ Some not done
    ▼                   ▼
Allow transition    Show warning
                    with list of
                    blocking behaviors
```

### Time Tracking Flow

```
Timer active on behavior
              │
              ▼
    ┌─────────────────────┐
    │  TimerManager tracks│
    │  - Start timestamp  │
    │  - Accumulated time │
    │  - Current session  │
    └─────────────────────┘
              │
              ▼
    Behavior marked done
              │
              ▼
    ┌─────────────────────┐
    │  Calculate total    │
    │  - Sum all sessions │
    │  - Save to actual_  │
    │    duration         │
    │  - Set end_time     │
    └─────────────────────┘
              │
              ▼
    Compare planned vs actual
    Generate efficiency report
```

## Configuration Management

```typescript
// src/config/defaults.ts
export const defaultConfig = {
  // Directory structure
  workspaceRoot: './workspaces',
  dataDir: './data',
  backupDir: './backups',
  classesDir: './classes',

  // Behavior settings
  defaultPriority: 'medium',
  defaultPlannedDuration: 60,  // Default estimated time in minutes (1 hour)
  maxDepth: 5,  // Max tree depth

  // Time tracking settings
  timeTracking: {
    enabled: true,                    // Enable automatic time tracking
    autoStartOnDoing: true,           // Auto-start timer when status -> doing
    autoStopOnDone: true,             // Auto-stop timer when status -> done
    showReminders: true,              // Show reminders for overdue behaviors
    reminderIntervals: [15, 5, 1],    // Minutes before deadline to remind
    pomodoroLength: 25,               // Default pomodoro length in minutes
    breakLength: 5,                   // Default break length in minutes
  },

  // Dependency settings
  dependencies: {
    allowForceStart: true,            // Allow starting with --force even if deps not done
    checkOnStart: true,               // Check dependencies before allowing start
    showInTree: true,                 // Show dependencies in tree view
  },

  // Acceptance criteria settings
  acceptanceCriteria: {
    requiredBeforeDone: false,        // Require all criteria to be checked before marking done
    promptOnDone: true,               // Prompt to review criteria when marking done
  },

  // Time aggregation settings
  timeAggregation: {
    enabled: true,                    // Enable automatic time aggregation
    updateOnChange: true,             // Update totals when behavior changes
    batchSize: 100,                   // Batch size for recalculation
    cacheExpiration: 3600,            // Cache expiration in seconds (1 hour)
  },

  // Efficiency thresholds (for alerts/reports)
  efficiencyThresholds: {
    excellent: 80,                    // <= 80% is excellent (under budget)
    good: 100,                        // <= 100% is good
    warning: 120,                     // <= 120% is warning (slightly over)
    critical: 150,                    // > 150% is critical (way over budget)
  },

  // AI integration
  claudeContextFile: './.claude/CLAUDE.md',

  // Display settings
  itemsPerPage: 20,
  dateFormat: 'yyyy-MM-dd',
  timeFormat: 'HH:mm',              // 24-hour format

  // Workspace settings
  workspaceNesting: true,  // Whether to nest child behavior workspaces
  autoCreateReadme: true,  // Whether to auto-create README.md

  // Class settings
  officialRepo: 'https://github.com/ai-me/behavior-classes',
  systemClassesDir: './behavior-classes',
};

// User config overrides (~/.ai-me/config.json)
interface UserConfig {
  workspaceRoot?: string;
  defaultPriority?: Priority;
  defaultPlannedDuration?: number;
  dateFormat?: string;
  timeFormat?: string;
  timeTracking?: Partial<typeof defaultConfig.timeTracking>;
  timeAggregation?: Partial<typeof defaultConfig.timeAggregation>;
  efficiencyThresholds?: Partial<typeof defaultConfig.efficiencyThresholds>;
  dependencies?: Partial<typeof defaultConfig.dependencies>;
  acceptanceCriteria?: Partial<typeof defaultConfig.acceptanceCriteria>;
  workspaceNesting?: boolean;
  // ...
}
```

## Error Handling Strategy

```typescript
// Custom error types
class AIMeError extends Error {
  constructor(
    public code: ErrorCode,
    message: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
  }
}

enum ErrorCode {
  // Core errors
  BEHAVIOR_NOT_FOUND = 'BEHAVIOR_NOT_FOUND',
  CLASS_NOT_FOUND = 'CLASS_NOT_FOUND',
  INVALID_STATUS_TRANSITION = 'INVALID_STATUS_TRANSITION',
  WORKSPACE_CREATE_FAILED = 'WORKSPACE_CREATE_FAILED',
  DATABASE_ERROR = 'DATABASE_ERROR',
  NOT_INITIALIZED = 'NOT_INITIALIZED',
  IMPORT_FAILED = 'IMPORT_FAILED',
  EXPORT_FAILED = 'EXPORT_FAILED',
  TREE_TOO_DEEP = 'TREE_TOO_DEEP',
  VERSION_CONFLICT = 'VERSION_CONFLICT',

  // Validation errors
  VALIDATION_FAILED = 'VALIDATION_FAILED',
  INVALID_DATE_FORMAT = 'INVALID_DATE_FORMAT',
  INVALID_PLANNED_DURATION = 'INVALID_PLANNED_DURATION',

  // Dependency errors
  DEPENDENCY_NOT_FOUND = 'DEPENDENCY_NOT_FOUND',
  DEPENDENCY_ALREADY_EXISTS = 'DEPENDENCY_ALREADY_EXISTS',
  CIRCULAR_DEPENDENCY = 'CIRCULAR_DEPENDENCY',
  DEPENDENCIES_NOT_SATISFIED = 'DEPENDENCIES_NOT_SATISFIED',
  CANNOT_START_BLOCKED = 'CANNOT_START_BLOCKED',

  // Time tracking errors
  TIMER_ALREADY_RUNNING = 'TIMER_ALREADY_RUNNING',
  TIMER_NOT_RUNNING = 'TIMER_NOT_RUNNING',
  INVALID_DURATION = 'INVALID_DURATION',
  DEADLINE_IN_PAST = 'DEADLINE_IN_PAST',

  // Acceptance criteria errors
  CRITERION_NOT_FOUND = 'CRITERION_NOT_FOUND',
  CRITERIA_NOT_MET = 'CRITERIA_NOT_MET',
  ACCEPTANCE_CHECK_FAILED = 'ACCEPTANCE_CHECK_FAILED',
}

// Error messages with i18n support
const errorMessages: Record<ErrorCode, LocalizedText> = {
  [ErrorCode.DEPENDENCIES_NOT_SATISFIED]: {
    en: 'Cannot start behavior: dependencies not satisfied',
    zh: '无法开始行为：依赖条件未满足'
  },
  [ErrorCode.CIRCULAR_DEPENDENCY]: {
    en: 'Cannot add dependency: would create circular dependency',
    zh: '无法添加依赖：会形成循环依赖'
  },
  [ErrorCode.CRITERIA_NOT_MET]: {
    en: 'Cannot complete behavior: acceptance criteria not met',
    zh: '无法完成行为：验收条件未满足'
  },
  // ... more messages
};

// CLI layer unified error handling
function handleError(error: unknown) {
  if (error instanceof AIMeError) {
    console.error(chalk.red(`Error [${error.code}]: ${error.message}`));
    if (error.details) {
      console.error(chalk.gray(JSON.stringify(error.details, null, 2)));
    }
  } else {
    console.error(chalk.red('Unexpected error:'), error);
  }
  process.exit(1);
}
```

## Extension Points

1. **Plugin System**: Reserved hooks for future custom plugins
2. **Export Formats**: Support JSON/YAML/Markdown export
3. **Sync Interface**: Reserved cloud sync interface (not in initial version)
4. **Notification Interface**: Reserved completion/deadline reminders
