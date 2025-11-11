/**
 * Project Service
 *
 * Provides business logic for project operations.
 * Used by all JetBrains plugins (IntelliJ, PyCharm, WebStorm).
 */

package com.socrates2.services

import com.socrates2.api.*
import kotlinx.coroutines.*

class ProjectService(
    private val apiClient: SocratesApiClient
) {
    /**
     * Load all projects for current user
     */
    suspend fun loadProjects(): Result<List<Project>> = runCatching {
        apiClient.getProjects()
    }

    /**
     * Load single project with all details
     */
    suspend fun loadProjectDetails(projectId: String): Result<ProjectDetails> =
        runCatching {
            val project = apiClient.getProject(projectId)
            val specifications = apiClient.getSpecifications(projectId)
            val conflicts = apiClient.getConflicts(projectId)
            val activity = apiClient.getActivity(projectId)

            ProjectDetails(
                project = project,
                specifications = specifications,
                conflicts = conflicts,
                activity = activity,
                specificationCount = specifications.size,
                conflictCount = conflicts.filter { !it.resolved }.size,
                maturityPercentage = project.maturityScore
            )
        }

    /**
     * Create new project
     */
    suspend fun createProject(name: String, description: String): Result<Project> =
        runCatching {
            if (name.isBlank()) throw IllegalArgumentException("Project name cannot be empty")
            if (name.length > 100) throw IllegalArgumentException("Project name too long (max 100 chars)")

            apiClient.createProject(name, description)
        }

    /**
     * Update project
     */
    suspend fun updateProject(
        projectId: String,
        name: String? = null,
        description: String? = null
    ): Result<Project> = runCatching {
        if (name != null) {
            if (name.isBlank()) throw IllegalArgumentException("Project name cannot be empty")
            if (name.length > 100) throw IllegalArgumentException("Project name too long")
        }

        apiClient.updateProject(projectId, name, description)
    }

    /**
     * Delete project (with confirmation)
     */
    suspend fun deleteProject(projectId: String): Result<Unit> = runCatching {
        apiClient.deleteProject(projectId)
    }

    /**
     * Get maturity assessment
     */
    suspend fun getMaturityScore(projectId: String): Result<MaturityAssessment> =
        runCatching {
            val project = apiClient.getProject(projectId)
            val specifications = apiClient.getSpecifications(projectId)
            val conflicts = apiClient.getConflicts(projectId)

            MaturityAssessment(
                projectId = projectId,
                score = project.maturityScore,
                specificationCount = specifications.size,
                completedCount = specifications.filter { !it.value.isEmpty() }.size,
                conflictCount = conflicts.filter { !it.resolved }.size,
                assessmentDate = System.currentTimeMillis()
            )
        }

    /**
     * Get project statistics
     */
    suspend fun getProjectStats(projectId: String): Result<ProjectStats> =
        runCatching {
            val project = apiClient.getProject(projectId)
            val specifications = apiClient.getSpecifications(projectId)
            val conflicts = apiClient.getConflicts(projectId)
            val activity = apiClient.getActivity(projectId)

            // Group specifications by category
            val specsByCategory = specifications.groupingBy { it.category }
                .eachCount()

            // Calculate conflict severity distribution
            val conflictBySeverity = conflicts.groupingBy { it.type }
                .eachCount()

            ProjectStats(
                projectId = projectId,
                totalSpecifications = specifications.size,
                totalConflicts = conflicts.size,
                unresolvedConflicts = conflicts.filter { !it.resolved }.size,
                resolvedConflicts = conflicts.filter { it.resolved }.size,
                specificationsByCategory = specsByCategory,
                conflictsBySeverity = conflictBySeverity,
                totalActivity = activity.size,
                maturityScore = project.maturityScore
            )
        }

    /**
     * Search projects
     */
    suspend fun searchProjects(query: String): Result<List<Project>> =
        runCatching {
            val allProjects = apiClient.getProjects()
            allProjects.filter { project ->
                project.name.contains(query, ignoreCase = true) ||
                    project.description.contains(query, ignoreCase = true)
            }
        }

    /**
     * Export project to file
     */
    suspend fun exportProject(projectId: String, format: String): Result<String> =
        runCatching {
            if (format !in listOf("json", "yaml", "csv")) {
                throw IllegalArgumentException("Unsupported format: $format")
            }
            // Would call API endpoint in full implementation
            "{}"
        }
}

// ============ Data Models ============

data class ProjectDetails(
    val project: Project,
    val specifications: List<Specification>,
    val conflicts: List<Conflict>,
    val activity: List<Activity>,
    val specificationCount: Int,
    val conflictCount: Int,
    val maturityPercentage: Int
)

data class MaturityAssessment(
    val projectId: String,
    val score: Int,
    val specificationCount: Int,
    val completedCount: Int,
    val conflictCount: Int,
    val assessmentDate: Long
)

data class ProjectStats(
    val projectId: String,
    val totalSpecifications: Int,
    val totalConflicts: Int,
    val unresolvedConflicts: Int,
    val resolvedConflicts: Int,
    val specificationsByCategory: Map<String, Int>,
    val conflictsBySeverity: Map<String, Int>,
    val totalActivity: Int,
    val maturityScore: Int
)
