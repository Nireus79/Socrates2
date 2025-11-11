/**
 * Conflict Detection Inspection
 *
 * IntelliJ IDEA inspection provider for detecting specification conflicts.
 */

package com.socrates2.inspections

import com.intellij.codeInspection.*
import com.intellij.openapi.project.Project
import com.intellij.psi.PsiFile
import com.intellij.psi.PsiElement
import com.socrates2.api.SocratesApiClient
import com.socrates2.services.ProjectService
import kotlinx.coroutines.*


class ConflictInspection : LocalInspectionTool() {

    override fun getDisplayName(): String = "Socrates2 Specification Conflicts"

    override fun getShortName(): String = "SocratesConflict"

    override fun getGroupDisplayName(): String = "Socrates2"

    override fun isEnabledByDefault(): Boolean = true

    override fun getDefaultLevel(): HighlightDisplayLevel = HighlightDisplayLevel.WARNING

    override fun buildVisitor(
        holder: ProblemsHolder,
        isOnTheFly: Boolean
    ): com.intellij.psi.PsiElementVisitor {
        return ConflictVisitor(holder, holder.project)
    }
}

class ConflictVisitor(
    private val holder: ProblemsHolder,
    private val project: Project
) : com.intellij.psi.PsiElementVisitor() {

    private val scope = CoroutineScope(Dispatchers.Default + SupervisorJob())

    override fun visitFile(file: PsiFile) {
        super.visitFile(file)

        // Check for specification references in the file
        val projectId = getProjectIdFromContext() ?: return
        checkConflicts(file, projectId)
    }

    private fun checkConflicts(file: PsiFile, projectId: String) {
        scope.launch {
            try {
                // Get API client from project service
                // Would integrate with actual ProjectService

                // Extract project-specific info from file context
                val fileContent = file.text

                // Check for patterns like @spec or specification names
                val specPatterns = Regex("""@spec\(['""]([^'"" ]+)['""]\)|spec[_-]([a-zA-Z0-9._-]+)""")
                val matches = specPatterns.findAll(fileContent)

                matches.forEach { match ->
                    val specKey = match.groupValues[1].ifEmpty { match.groupValues[2] }

                    // Would fetch conflicts from API
                    // For now, just demonstrate the inspection structure

                    if (specKey.contains("deprecated")) {
                        val offset = match.range.first
                        val element = file.findElementAt(offset)
                        if (element != null) {
                            holder.registerProblem(
                                element,
                                "Specification '$specKey' is deprecated",
                                ProblemHighlightType.WARNING,
                                *arrayOf(
                                    UpdateDeprecatedSpecQuickFix(specKey),
                                    ViewConflictQuickFix(specKey)
                                )
                            )
                        }
                    }
                }
            } catch (e: Exception) {
                // Silent fail for inspection
            }
        }
    }

    private fun getProjectIdFromContext(): String? {
        // Would get project ID from workspace metadata
        // For now, return null
        return null
    }
}

class UpdateDeprecatedSpecQuickFix(private val specKey: String) : LocalQuickFix {

    override fun getFamilyName(): String = "Update deprecated specification"

    override fun getName(): String = "Update '$specKey' to latest version"

    override fun applyFix(project: Project, descriptor: ProblemDescriptor) {
        // Would show dialog to select replacement specification
        // or provide code action for replacement
    }
}

class ViewConflictQuickFix(private val specKey: String) : LocalQuickFix {

    override fun getFamilyName(): String = "View conflict details"

    override fun getName(): String = "View conflict for '$specKey'"

    override fun applyFix(project: Project, descriptor: ProblemDescriptor) {
        // Would open Socrates2 tool window showing conflict details
    }
}
