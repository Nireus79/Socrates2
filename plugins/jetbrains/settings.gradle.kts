rootProject.name = "socrates2-jetbrains"

include(":intellij", ":pycharm", ":webstorm")

project(":intellij").projectDir = file("intellij")
project(":pycharm").projectDir = file("pycharm")
project(":webstorm").projectDir = file("webstorm")
