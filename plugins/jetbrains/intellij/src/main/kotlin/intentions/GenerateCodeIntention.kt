/**
 * Generate Code Intention Action
 *
 * IntelliJ IDEA intention for generating code from specifications.
 */

package com.socrates2.intentions

import com.intellij.codeInsight.intention.IntentionAction
import com.intellij.codeInsight.intention.PsiElementBaseIntentionAction
import com.intellij.openapi.editor.Editor
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.ComboBox
import com.intellij.openapi.ui.DialogWrapper
import com.intellij.psi.PsiElement
import com.intellij.util.IncorrectOperationException
import com.socrates2.api.SocratesApiClient
import com.socrates2.services.CodeGeneratorService
import kotlinx.coroutines.*
import javax.swing.DefaultComboBoxModel
import javax.swing.JComponent
import javax.swing.JPanel
import javax.swing.JLabel
import javax.swing.BoxLayout
import com.intellij.util.ui.JBUI


class GenerateCodeIntention : PsiElementBaseIntentionAction() {

    override fun getText(): String = "Generate code from specification"

    override fun getFamilyName(): String = "Socrates2"

    override fun startInWriteAction(): Boolean = false

    override fun isAvailable(project: Project, editor: Editor?, element: PsiElement?): Boolean {
        if (element == null) return false

        // Check if element contains a specification reference
        val text = element.text
        return text.contains(Regex("""@spec|specification|spec_"""))
    }

    @Throws(IncorrectOperationException::class)
    override fun invoke(project: Project, editor: Editor?, element: PsiElement?) {
        if (editor == null || element == null) return

        // Extract specification identifier from element
        val specId = extractSpecificationId(element.text) ?: return

        // Get the API client (would be injected in real implementation)
        val apiClient = SocratesApiClient("http://localhost:8000", authManager = null as Any as com.socrates2.api.AuthManager)
        val codeGenService = CodeGeneratorService(apiClient)

        // Show language selection dialog
        val dialog = LanguageSelectionDialog(project, codeGenService)
        if (dialog.showAndGet()) {
            val language = dialog.selectedLanguage
            generateAndInsertCode(project, editor, specId, language, codeGenService)
        }
    }

    private fun extractSpecificationId(text: String): String? {
        // Extract spec ID from patterns like @spec("id") or spec_key
        val patterns = listOf(
            Regex("""@spec\(['""]([^'"" ]+)['""]\)"""),
            Regex("""spec[_-]([a-zA-Z0-9._-]+)""")
        )

        return patterns.mapNotNull { it.find(text)?.groupValues?.getOrNull(1) }.firstOrNull()
    }

    private fun generateAndInsertCode(
        project: Project,
        editor: Editor,
        specId: String,
        language: String,
        codeGenService: CodeGeneratorService
    ) {
        CoroutineScope(Dispatchers.Main).launch {
            try {
                val result = codeGenService.generateCode(specId, language)
                result.onSuccess { generated ->
                    // Insert code at cursor position
                    val document = editor.document
                    val offset = editor.caretModel.offset
                    document.insertString(offset, generated.code)
                }.onFailure { error ->
                    com.intellij.openapi.ui.Messages.showErrorDialog(
                        project,
                        "Failed to generate code: ${error.message}",
                        "Error"
                    )
                }
            } catch (e: Exception) {
                com.intellij.openapi.ui.Messages.showErrorDialog(
                    project,
                    "Code generation failed: ${e.message}",
                    "Error"
                )
            }
        }
    }
}

class LanguageSelectionDialog(
    project: Project,
    private val codeGenService: CodeGeneratorService
) : DialogWrapper(project) {

    private val languageCombo = ComboBox<String>()
    var selectedLanguage: String = "python"
        private set

    init {
        title = "Select Language"
        init()
        setupLanguages()
    }

    private fun setupLanguages() {
        val languages = codeGenService.getSupportedLanguages()
        val languageNames = languages.map { it.name }
        languageCombo.model = DefaultComboBoxModel(languageNames.toTypedArray())
        languageCombo.selectedIndex = 0

        languageCombo.addActionListener {
            val selected = languageCombo.selectedItem as? String
            if (selected != null) {
                val lang = languages.find { it.name == selected }
                if (lang != null) {
                    selectedLanguage = lang.id
                }
            }
        }
    }

    override fun createCenterPanel(): JComponent {
        return JPanel().apply {
            layout = BoxLayout(this, BoxLayout.Y_AXIS)
            border = JBUI.Borders.empty(10)
            add(JLabel("Select target language:"))
            add(languageCombo)
        }
    }
}

/**
 * Alternative simple intention without dialog
 */
class QuickGeneratePythonIntention : IntentionAction {

    override fun getText(): String = "Generate Python code"

    override fun getFamilyName(): String = "Socrates2"

    override fun startInWriteAction(): Boolean = false

    override fun isAvailable(project: Project, editor: Editor?, file: com.intellij.psi.PsiFile?): Boolean {
        if (editor == null) return false
        val element = file?.findElementAt(editor.caretModel.offset) ?: return false
        return element.text.contains(Regex("""@spec|specification"""))
    }

    override fun invoke(project: Project, editor: Editor?, file: com.intellij.psi.PsiFile?) {
        // Would generate Python code directly without dialog
        if (editor == null || file == null) return

        // Implementation similar to GenerateCodeIntention but fixed to Python
    }
}
