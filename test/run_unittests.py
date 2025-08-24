import os
import subprocess
import sys

IGNORE_FILES = [
    "__init__.py",
    "test_run_all_tests.py"
]

def run_tests_in_dir(test_dir="test/unittest"):
    project_root = os.path.dirname(os.path.abspath(__file__))
    # 确保 src 在 sys.path 中
    sys.path.insert(0, project_root)

    # 收集 test 目录下所有 .py 文件
    test_files = []
    for root, _, files in os.walk(test_dir):
        for file in files:
            if file.endswith(".py") and file not in IGNORE_FILES:
                test_files.append(os.path.join(root, file))

    if not test_files:
        print(f"❌ No test files found in {test_dir}")
        sys.exit(1)

    print(f"🔎 Found {len(test_files)} test files. Running them one by one...\n")

    failed = []
    for test_file in test_files:
        print(f"▶ Running {test_file} ...")
        env = os.environ.copy()
        # 重点：在子进程里也传递 PYTHONPATH
        env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")
        result = subprocess.run([sys.executable, test_file], capture_output=True, text=True, encoding='utf-8', env=env)

        if result.returncode == 0:
            print(f"✅ {test_file} [PASSED]\n")
        else:
            print(f"❌ {test_file} [FAILED]\n--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}")
            failed.append(test_file)

    if failed:
        print(f"\n❌ {len(failed)} test(s) failed:")
        for f in failed:
            print(f"   - {f}")
        sys.exit(1)
    else:
        print("\n🎉 All tests passed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    run_tests_in_dir("test/unittest")