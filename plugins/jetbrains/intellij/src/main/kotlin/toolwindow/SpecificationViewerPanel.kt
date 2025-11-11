/**
 * Specification Viewer Tool Window Panel
 *
 * IntelliJ IDEA plugin component for viewing and managing specifications.
 */

package com.socrates2.toolwindow

import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.SimpleToolWindowPanel
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.treeStructure.Tree
import com.intellij.util.ui.JBUI
import com.socrates2.api.SocratesApiClient
import com.socrates2.api.Specification
import com.socrates2.services.SpecificationService
import kotlinx.coroutines.*
import javax.swing.*
import javax.swing.tree.DefaultMutableTreeNode
import javax.swing.tree.DefaultTreeModel


class SpecificationViewerPanel(
    private val ideaProject: Project,
    private val apiClient: SocratesApiClient
) : SimpleToolWindowPanel(true, true) {

    private val specService = SpecificationService(apiClient)
    private val specTree = Tree(DefaultMutableTreeNode("Specifications"))
    private val searchField = JTextField(20)
    private val refreshButton = JButton("Refresh")
    private val statusLabel = JLabel("Select a project to view specifications")
    private val detailsPanel = SpecificationDetailsPanel()
    private var scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private var currentProjectId: String? = null

    init {
        setupUI()
        setupListeners()
    }

    private fun setupUI() {
        // Toolbar
        val toolbar = JPanel().apply {
            layout = BoxLayout(this, BoxLayout.X_AXIS)
            border = JBUI.Borders.empty(5)
            add(JLabel("Search:"))
            add(Box.createHorizontalStrut(5))
            add(searchField)
            add(Box.createHorizontalStrut(5))
            add(refreshButton)
            add(Box.createHorizontalGlue())
        }

        // Spec tree
        specTree.apply {
            emptyText.text = "No specifications found"
            isRootVisible = true
        }

        // Split pane
        val splitPane = JSplitPane(
            JSplitPane.HORIZONTAL_SPLIT,
            JBScrollPane(specTree),
            detailsPanel
        ).apply {
            dividerLocation = 300
            resizeWeight = 0.3
        }

        // Status
        statusLabel.apply {
            border = JBUI.Borders.empty(5)
            font = font.deriveFont(11f)
        }

        // Layout
        setToolbar(toolbar)
        setContent(splitPane)
        add(statusLabel, BorderLayout.SOUTH)
    }

    private fun setupListeners() {
        refreshButton.addActionListener {
            currentProjectId?.let { projectId ->
                loadSpecifications(projectId)
            }
        }

        searchField.apply {
            addActionListener {
                currentProjectId?.let { projectId ->
                    searchSpecifications(projectId, text)
                }
            }
        }

        specTree.addTreeSelectionListener { event ->
            val selectedNode = event.path.lastPathComponent as? DefaultMutableTreeNode
            if (selectedNode != null && selectedNode.userObject is Specification) {
                val spec = selectedNode.userObject as Specification
                detailsPanel.showSpecification(spec)
            }
        }
    }

    fun loadSpecificationsForProject(projectId: String) {
        currentProjectId = projectId
        searchField.text = ""
        loadSpecifications(projectId)
    }

    private fun loadSpecifications(projectId: String) {
        scope.launch {
            try {
                statusLabel.text = "Loading specifications..."
                refreshButton.isEnabled = false

                val result = specService.loadSpecificationsByCategory(projectId)
                result.onSuccess { specsByCategory ->
                    updateSpecificationTree(specsByCategory)
                    statusLabel.text = "Specifications: ${specsByCategory.values.sumOf { it.size }}"
                    refreshButton.isEnabled = true
                }.onFailure { error ->
                    statusLabel.text = "Error: ${error.message}"
                    refreshButton.isEnabled = true
                }
            } catch (e: Exception) {
                statusLabel.text = "Error loading specifications"
                refreshButton.isEnabled = true
            }
        }
    }

    private fun searchSpecifications(projectId: String, query: String) {
        if (query.isEmpty()) {
            loadSpecifications(projectId)
            return
        }

        scope.launch {
            try {
                statusLabel.text = "Searching..."
                refreshButton.isEnabled = false

                val result = specService.searchSpecifications(projectId, query)
                result.onSuccess { specs ->
                    val grouped = specs.groupBy { it.category }
                    updateSpecificationTree(grouped)
                    statusLabel.text = "Found: ${specs.size} specifications"
                    refreshButton.isEnabled = true
                }.onFailure { error ->
                    statusLabel.text = "Error: ${error.message}"
                    refreshButton.isEnabled = true
                }
            } catch (e: Exception) {
                statusLabel.text = "Error searching specifications"
                refreshButton.isEnabled = true
            }
        }
    }

    private fun updateSpecificationTree(specsByCategory: Map<String, List<Specification>>) {
        val rootNode = DefaultMutableTreeNode("Specifications")

        specsByCategory.forEach { (category, specs) ->
            val categoryNode = DefaultMutableTreeNode(category)
            specs.forEach { spec ->
                val specNode = DefaultMutableTreeNode(spec)
                categoryNode.add(specNode)
            }
            rootNode.add(categoryNode)
        }

        specTree.model = DefaultTreeModel(rootNode)
        (0 until specTree.rowCount).forEach { specTree.expandRow(it) }
    }

    fun dispose() {
        scope.cancel()
        detailsPanel.dispose()
    }
}

/**
 * Panel for displaying specification details
 */
class SpecificationDetailsPanel : JPanel() {

    private val keyLabel = JLabel()
    private val valueArea = JTextArea().apply {
        lineWrap = true
        wrapStyleWord = true
        isEditable = false
    }
    private val categoryLabel = JLabel()
    private val generatedCodeArea = JTextArea().apply {
        lineWrap = true
        wrapStyleWord = true
        isEditable = false
    }
    private val generateButton = JButton("Generate Code")
    private val copyButton = JButton("Copy")

    init {
        layout = BoxLayout(this, BoxLayout.Y_AXIS)
        border = JBUI.Borders.empty(10)

        // Key
        add(JLabel("Key:").apply { font = font.deriveFont(java.awt.Font.BOLD) })
        add(keyLabel)
        add(Box.createVerticalStrut(10))

        // Value
        add(JLabel("Value:").apply { font = font.deriveFont(java.awt.Font.BOLD) })
        add(JBScrollPane(valueArea).apply {
            preferredSize = java.awt.Dimension(0, 80)
        })
        add(Box.createVerticalStrut(10))

        // Category
        add(JLabel("Category:").apply { font = font.deriveFont(java.awt.Font.BOLD) })
        add(categoryLabel)
        add(Box.createVerticalStrut(10))

        // Generated code
        add(JLabel("Generated Code:").apply { font = font.deriveFont(java.awt.Font.BOLD) })
        add(JBScrollPane(generatedCodeArea).apply {
            preferredSize = java.awt.Dimension(0, 150)
        })
        add(Box.createVerticalStrut(10))

        // Buttons
        val buttonPanel = JPanel().apply {
            layout = BoxLayout(this, BoxLayout.X_AXIS)
            add(generateButton)
            add(Box.createHorizontalStrut(5))
            add(copyButton)
            add(Box.createHorizontalGlue())
        }
        add(buttonPanel)
    }

    fun showSpecification(spec: Specification) {
        keyLabel.text = spec.key
        valueArea.text = spec.value
        categoryLabel.text = spec.category
        generatedCodeArea.text = "Generate code to see output..."
    }

    fun dispose() {
        // Cleanup
    }
}
