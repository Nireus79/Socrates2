package com.socrates2.pycharm.extensions

import com.intellij.openapi.project.Project
import com.intellij.psi.PsiElement
import com.intellij.psi.PsiFile
import com.jetbrains.python.psi.PyFile
import com.jetbrains.python.psi.PyClass
import com.jetbrains.python.psi.PyFunction
import com.jetbrains.python.psi.PyStatement
import com.socrates2.jetbrains.common.api.client.SocratesApiClient
import com.socrates2.jetbrains.common.services.CodeGeneratorService
import kotlinx.coroutines.runBlocking
import java.io.File

/**
 * Python-specific code generation extension
 *
 * Provides Python-specific patterns and generators:
 * - dataclass generation
 * - async/await patterns
 * - type hints and protocols
 * - pytest integration
 */
class PythonCodeGenerationExtension(
    private val project: Project,
    private val codeGeneratorService: CodeGeneratorService
) {
    /**
     * Generate dataclass from specification
     */
    fun generateDataclass(specificationId: String): String = runBlocking {
        val options = mapOf(
            "dataclass" to "true",
            "typing" to "true",
            "slots" to "false"
        )

        val result = codeGeneratorService.generateCode(
            specificationId,
            "python",
            options
        )

        return@runBlocking result.getOrNull()?.code ?: ""
    }

    /**
     * Generate async class from specification
     */
    fun generateAsyncClass(specificationId: String): String = runBlocking {
        val options = mapOf(
            "async" to "true",
            "typing" to "true",
            "error_handling" to "exceptions"
        )

        val result = codeGeneratorService.generateCode(
            specificationId,
            "python",
            options
        )

        return@runBlocking result.getOrNull()?.code ?: ""
    }

    /**
     * Generate type hints for class members
     */
    fun generateTypeHints(pyClass: PyClass): String {
        val builder = StringBuilder()
        builder.append("from typing import Any, Dict, List, Optional\n\n")

        // Extract members and generate type hints
        val members = extractClassMembers(pyClass)
        for ((name, type) in members) {
            builder.append("$name: $type\n")
        }

        return builder.toString()
    }

    /**
     * Generate test class from specification
     */
    fun generateTestClass(specificationId: String, className: String): String {
        return """
import pytest
from typing import Any
from .${className.lowercase()} import $className


class Test$className:
    """Test cases for $className"""

    @pytest.fixture
    def instance(self) -> $className:
        """Create test instance"""
        return $className()

    def test_creation(self, instance: $className) -> None:
        """Test instance creation"""
        assert instance is not None

    def test_validation(self, instance: $className) -> None:
        """Test validation"""
        assert instance.validate()

    @pytest.mark.asyncio
    async def test_async_operation(self, instance: $className) -> None:
        """Test async operations"""
        result = await instance.fetch_data()
        assert result is not None


class TestIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_full_workflow(self) -> None:
        """Test complete workflow"""
        instance = $className()
        assert instance.validate()
""".trimIndent()
    }

    /**
     * Generate protocol/ABC for interface definition
     */
    fun generateProtocol(specificationId: String): String {
        return """
from abc import ABC, abstractmethod
from typing import Any, Dict


class ProtocolInterface(ABC):
    """Interface protocol definition"""

    @abstractmethod
    def execute(self) -> Any:
        """Execute operation"""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate state"""
        pass
""".trimIndent()
    }

    /**
     * Analyze Python file for specifications
     */
    fun analyzeSpecifications(file: PsiFile): List<SpecificationReference> {
        val references = mutableListOf<SpecificationReference>()

        if (file !is PyFile) return references

        // Search for @spec, @specification, spec() patterns
        file.acceptChildren(object : PyElementVisitor {
            override fun visitPyElement(element: PsiElement) {
                when {
                    element is PyClass -> analyzeClass(element, references)
                    element is PyFunction -> analyzeFunction(element, references)
                }
                element.acceptChildren(this)
            }
        })

        return references
    }

    private fun analyzeClass(pyClass: PyClass, references: MutableList<SpecificationReference>) {
        val docstring = pyClass.docStringValue
        if (docstring != null) {
            extractSpecReferences(docstring, references)
        }
    }

    private fun analyzeFunction(pyFunc: PyFunction, references: MutableList<SpecificationReference>) {
        val docstring = pyFunc.docStringValue
        if (docstring != null) {
            extractSpecReferences(docstring, references)
        }
    }

    private fun extractSpecReferences(text: String, references: MutableList<SpecificationReference>) {
        // Match @spec.key, @specification.key patterns
        val specPattern = """@(?:spec|specification)\.(\w+(?:\.\w+)*)""".toRegex()
        val matches = specPattern.findAll(text)

        for (match in matches) {
            references.add(
                SpecificationReference(
                    key = match.groupValues[1],
                    line = text.substringBefore(match.value).count { it == '\n' }
                )
            )
        }
    }

    private fun extractClassMembers(pyClass: PyClass): Map<String, String> {
        val members = mutableMapOf<String, String>()

        // Extract member types from annotations or defaults
        for (stmt in pyClass.stmtList) {
            when (stmt) {
                is PyStatement -> {
                    // Extract variable and type hint
                    val text = stmt.text
                    if (":" in text) {
                        val parts = text.split(":")
                        if (parts.size >= 2) {
                            val name = parts[0].trim()
                            val type = parts[1].split("=")[0].trim()
                            members[name] = type
                        }
                    }
                }
            }
        }

        return members
    }

    /**
     * Python-specific code style formatter
     */
    fun formatPythonCode(code: String): String {
        val lines = code.split("\n")
        val formatted = mutableListOf<String>()
        var indentLevel = 0

        for (line in lines) {
            val stripped = line.trim()

            // Decrease indent for closing
            if (stripped.isEmpty() || stripped.startsWith("class ") || stripped.startsWith("def ")) {
                if (stripped.startsWith("class ") || stripped.startsWith("def ")) {
                    indentLevel = 0
                }
            }

            if (stripped.isNotEmpty()) {
                formatted.add("    ".repeat(indentLevel) + stripped)
            } else {
                formatted.add("")
            }

            // Increase indent for blocks
            if (stripped.endsWith(":")) {
                indentLevel++
            }
        }

        return formatted.joinToString("\n")
    }
}

/**
 * Visitor for Python elements
 */
open class PyElementVisitor {
    open fun visitPyElement(element: PsiElement) {}
}

/**
 * Specification reference found in Python code
 */
data class SpecificationReference(
    val key: String,
    val line: Int
)
