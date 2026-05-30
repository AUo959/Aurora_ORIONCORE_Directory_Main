// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "AuroraMacStarter",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(name: "aurora-macos-starter", targets: ["AuroraMacStarter"]),
        .library(name: "AuroraMacStarterCore", targets: ["AuroraMacStarterCore"])
    ],
    targets: [
        .target(name: "AuroraMacStarterCore"),
        .executableTarget(
            name: "AuroraMacStarter",
            dependencies: ["AuroraMacStarterCore"]
        )
    ]
)
