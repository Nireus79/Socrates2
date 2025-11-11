/**
 * Project Browser Tool Window Panel
 *
 * IntelliJ IDEA plugin component for browsing and managing projects.
 */

package com.socrates2.toolwindow

import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.SimpleToolWindowPanel
import com.intellij.ui.components.JBList
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.treeStructure.Tree
import com.intellij.util.ui.JBUI
import com.socrates2.api.SocratesApiClient
import com.socrates2.services.ProjectService
import kotlinx.coroutines.*
import javax.swing.*
import javax.swing.tree.DefaultMutableTreeNode
import javax.swing.tree.DefaultTreeModel


class ProjectBrowserPanel(
    private val ideaProject: Project,
    private val apiClient: SocratesApiClient
) : SimpleToolWindowPanel(true, true) {

    private val projectService = ProjectService(apiClient)
    private val projectTree = Tree(DefaultMutableTreeNode("Projects"))
    private val refreshButton = JButton("Refresh")
    private val createButton = JButton("New Project")
    private val statusLabel = JLabel("Loading projects...")
    private var scope = CoroutineScope(Dispatchers.Main + SupervisorJob())

    init {
        setupUI()
        setupListeners()
        loadProjects()
    }

    private fun setupUI() {
        // Toolbar
        val toolbar = JPanel().apply {
            layout = BoxLayout(this, BoxLayout.X_AXIS)
            border = JBUI.Borders.empty(5)
            add(refreshButton)
            add(Box.createHorizontalStrut(5))
            add(createButton)
            add(Box.createHorizontalGlue())
        }

        // Tree
        projectTree.apply {
            emptyText.text = "No projects found"
            isRootVisible = true
        }

        val scrollPane = JBScrollPane(projectTree).apply {
            border = JBUI.Borders.empty()
        }

        // Status
        statusLabel.apply {
            border = JBUI.Borders.empty(5)
            font = font.deriveFont(11f)
        }

        // Layout
        setToolbar(toolbar)
        setContent(scrollPane)
        add(statusLabel, BorderLayout.SOUTH)
    }

    private fun setupListeners() {
        refreshButton.addActionListener {
            loadProjects()
        }

        createButton.addActionListener {
            showCreateProjectDialog()
        }

        projectTree.addTreeSelectionListener { event ->
            val selectedNode = event.path.lastPathComponent as? DefaultMutableTreeNode
            if (selectedNode != null) {
                handleProjectSelected(selectedNode)
            }
        }
    }

    private fun loadProjects() {
        scope.launch {
            try {
                statusLabel.text = "Loading projects..."
                refreshButton.isEnabled = false

                val result = projectService.loadProjects()
                result.onSuccess { projects ->
                    updateProjectTree(projects)
                    statusLabel.text = "Projects: ${projects.size}"
                    refreshButton.isEnabled = true
                }.onFailure { error ->
                    statusLabel.text = "Error: ${error.message}"
                    refreshButton.isEnabled = true
                    JOptionPane.showErrorDialog(
                        this@ProjectBrowserPanel,
                        "Failed to load projects: ${error.message}",
                        "Error",
                        JOptionPane.ERROR_MESSAGE
                    )
                }
            } catch (e: Exception) {
                statusLabel.text = "Error loading projects"
                refreshButton.isEnabled = true
            }
        }
    }

    private fun updateProjectTree(projects: List<com.socrates2.api.Project>) {
        val rootNode = DefaultMutableTreeNode("Projects")

        projects.forEach { project ->
            val projectNode = DefaultMutableTreeNode(
                ProjectTreeNode(
                    id = project.id,
                    name = project.name,
                    description = project.description,
                    maturityScore = project.maturityScore
                )
            )
            rootNode.add(projectNode)
        }

        projectTree.model = DefaultTreeModel(rootNode)
        (0 until projectTree.rowCount).forEach { projectTree.expandRow(it) }
    }

    private fun handleProjectSelected(node: DefaultMutableTreeNode) {
        val userObject = node.userObject
        if (userObject is ProjectTreeNode) {
            // Notify listeners or update other panels
            // Could trigger specification panel update
        }
    }

    private fun showCreateProjectDialog() {
        val nameInput = JTextField(20)
        val descriptionInput = JTextArea(5, 20)
        descriptionInput.lineWrap = true
        descriptionInput.wrapStyleWord = true

        val panel = JPanel(java.awt.GridBagLayout()).apply {
            val gbc = java.awt.GridBagConstraints()

            gbc.gridx = 0
            gbc.gridy = 0
            gbc.anchor = java.awt.GridBagConstraints.WEST
            add(JLabel("Project Name:"), gbc)

            gbc.gridx = 1
            add(nameInput, gbc)

            gbc.gridx = 0
            gbc.gridy = 1
            add(JLabel("Description:"), gbc)

            gbc.gridx = 1
            gbc.gridheight = 2
            add(JBScrollPane(descriptionInput), gbc)
        }

        val result = JOptionPane.showConfirmDialog(
            this,
            panel,
            "Create New Project",
            JOptionPane.OK_CANCEL_OPTION,
            JOptionPane.PLAIN_MESSAGE
        )

        if (result == JOptionPane.OK_OPTION) {
            val name = nameInput.text.trim()
            val description = descriptionInput.text.trim()

            if (name.isNotEmpty()) {
                scope.launch {
                    try {
                        statusLabel.text = "Creating project..."
                        val result = projectService.createProject(name, description)
                        result.onSuccess {
                            loadProjects()
                            JOptionPane.showMessageDialog(
                                this@ProjectBrowserPanel,
                                "Project created successfully",
                                "Success",
                                JOptionPane.INFORMATION_MESSAGE
                            )
                        }.onFailure { error ->
                            JOptionPane.showErrorDialog(
                                this@ProjectBrowserPanel,
                                "Failed to create project: ${error.message}",
                                "Error",
                                JOptionPane.ERROR_MESSAGE
                            )
                        }
                    } catch (e: Exception) {
                        statusLabel.text = "Error creating project"
                    }
                }
            }
        }
    }

    fun dispose() {
        scope.cancel()
    }
}

data class ProjectTreeNode(
    val id: String,
    val name: String,
    val description: String,
    val maturityScore: Int
) {
    override fun toString(): String = "$name (Maturity: $maturityScore%)"
}
