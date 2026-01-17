"""Performance benchmarks for TTS synthesis.

T066: Add performance benchmarks
"""

import asyncio
import statistics
import time
from dataclasses import dataclass

import pytest

from src.domain.entities.audio import AudioFormat, OutputMode
from src.domain.entities.tts import TTSRequest


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""

    name: str
    iterations: int
    total_time_ms: float
    mean_time_ms: float
    median_time_ms: float
    min_time_ms: float
    max_time_ms: float
    std_dev_ms: float
    throughput_per_second: float

    def __str__(self) -> str:
        return (
            f"Benchmark: {self.name}\n"
            f"  Iterations: {self.iterations}\n"
            f"  Total time: {self.total_time_ms:.2f} ms\n"
            f"  Mean: {self.mean_time_ms:.2f} ms\n"
            f"  Median: {self.median_time_ms:.2f} ms\n"
            f"  Min: {self.min_time_ms:.2f} ms\n"
            f"  Max: {self.max_time_ms:.2f} ms\n"
            f"  Std Dev: {self.std_dev_ms:.2f} ms\n"
            f"  Throughput: {self.throughput_per_second:.2f} req/s"
        )


def run_benchmark(
    name: str,
    func: callable,
    iterations: int = 100,
    warmup: int = 5,
) -> BenchmarkResult:
    """Run a synchronous benchmark.

    Args:
        name: Name of the benchmark
        func: Function to benchmark (should return execution time in ms)
        iterations: Number of iterations to run
        warmup: Number of warmup iterations (not counted)

    Returns:
        BenchmarkResult with statistics
    """
    # Warmup
    for _ in range(warmup):
        func()

    # Actual benchmark
    times: list[float] = []
    total_start = time.perf_counter()

    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    total_end = time.perf_counter()
    total_time_ms = (total_end - total_start) * 1000

    return BenchmarkResult(
        name=name,
        iterations=iterations,
        total_time_ms=total_time_ms,
        mean_time_ms=statistics.mean(times),
        median_time_ms=statistics.median(times),
        min_time_ms=min(times),
        max_time_ms=max(times),
        std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
        throughput_per_second=iterations / (total_time_ms / 1000),
    )


async def run_async_benchmark(
    name: str,
    func: callable,
    iterations: int = 100,
    warmup: int = 5,
) -> BenchmarkResult:
    """Run an async benchmark.

    Args:
        name: Name of the benchmark
        func: Async function to benchmark
        iterations: Number of iterations to run
        warmup: Number of warmup iterations (not counted)

    Returns:
        BenchmarkResult with statistics
    """
    # Warmup
    for _ in range(warmup):
        await func()

    # Actual benchmark
    times: list[float] = []
    total_start = time.perf_counter()

    for _ in range(iterations):
        start = time.perf_counter()
        await func()
        end = time.perf_counter()
        times.append((end - start) * 1000)

    total_end = time.perf_counter()
    total_time_ms = (total_end - total_start) * 1000

    return BenchmarkResult(
        name=name,
        iterations=iterations,
        total_time_ms=total_time_ms,
        mean_time_ms=statistics.mean(times),
        median_time_ms=statistics.median(times),
        min_time_ms=min(times),
        max_time_ms=max(times),
        std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
        throughput_per_second=iterations / (total_time_ms / 1000),
    )


class TestTTSRequestCreation:
    """Benchmark tests for TTSRequest creation."""

    def test_request_creation_performance(self) -> None:
        """Benchmark TTSRequest creation."""
        def create_request():
            return TTSRequest(
                text="Hello, this is a test.",
                voice_id="test-voice",
                provider="azure",
                language="en-US",
                speed=1.0,
                pitch=0.0,
                volume=1.0,
                output_format=AudioFormat.MP3,
                output_mode=OutputMode.BATCH,
            )

        result = run_benchmark(
            name="TTSRequest creation",
            func=create_request,
            iterations=1000,
        )

        print(f"\n{result}")

        # Assert reasonable performance
        assert result.mean_time_ms < 1.0, "Request creation should be < 1ms"
        assert result.throughput_per_second > 1000, "Should handle > 1000 req/s"

    def test_request_validation_performance(self) -> None:
        """Benchmark TTSRequest validation with various text lengths."""
        text_lengths = [100, 500, 1000, 2000, 5000]

        for length in text_lengths:
            text = "x" * length

            def create_request(text=text):
                return TTSRequest(
                    text=text,
                    voice_id="test-voice",
                    provider="azure",
                )

            result = run_benchmark(
                name=f"TTSRequest validation ({length} chars)",
                func=create_request,
                iterations=500,
            )

            print(f"\n{result}")

            # Validation should scale linearly
            assert result.mean_time_ms < 5.0, f"Validation for {length} chars should be < 5ms"


class TestConcurrentSynthesis:
    """Benchmark tests for concurrent request handling."""

    @pytest.mark.asyncio
    async def test_concurrent_request_creation(self) -> None:
        """Benchmark concurrent request creation."""
        async def create_many_requests():
            requests = []
            for i in range(10):
                req = TTSRequest(
                    text=f"Test message {i}",
                    voice_id="test-voice",
                    provider="azure",
                )
                requests.append(req)
            return requests

        result = await run_async_benchmark(
            name="Concurrent request creation (10 requests)",
            func=create_many_requests,
            iterations=100,
        )

        print(f"\n{result}")

        # Should handle concurrent creation efficiently
        assert result.mean_time_ms < 10.0, "Concurrent creation should be < 10ms"

    @pytest.mark.asyncio
    async def test_parallel_request_creation(self) -> None:
        """Benchmark parallel request creation using asyncio.gather."""
        async def create_request_async(i: int):
            await asyncio.sleep(0)  # Yield to event loop
            return TTSRequest(
                text=f"Test message {i}",
                voice_id="test-voice",
                provider="azure",
            )

        async def create_parallel():
            tasks = [create_request_async(i) for i in range(50)]
            return await asyncio.gather(*tasks)

        result = await run_async_benchmark(
            name="Parallel request creation (50 requests)",
            func=create_parallel,
            iterations=50,
        )

        print(f"\n{result}")

        # Parallel creation should be efficient
        assert result.mean_time_ms < 50.0, "Parallel creation should be < 50ms"


class TestTextProcessing:
    """Benchmark tests for text processing."""

    def test_special_character_handling(self) -> None:
        """Benchmark handling of special characters."""
        special_texts = [
            "Hello! How are you? 你好！",
            "Testing 1234567890 numbers",
            "Emoji test: 😀🎉🚀💯",
            "Mixed: Hello 世界 🌍 <tag> &amp;",
            "Long text with special chars: " + "test 测试 🔥 " * 100,
        ]

        for text in special_texts:
            def create_with_special(text=text):
                return TTSRequest(
                    text=text,
                    voice_id="test-voice",
                    provider="azure",
                )

            result = run_benchmark(
                name=f"Special char handling ({len(text)} chars)",
                func=create_with_special,
                iterations=500,
            )

            print(f"\n{result}")

            # Special characters shouldn't significantly impact performance
            assert result.mean_time_ms < 2.0, "Special char handling should be < 2ms"


class TestMemoryUsage:
    """Tests for memory efficiency."""

    def test_request_memory_footprint(self) -> None:
        """Test memory footprint of TTSRequest objects."""
        import sys

        # Create a single request
        request = TTSRequest(
            text="Test text",
            voice_id="test-voice",
            provider="azure",
        )

        # Get approximate size
        size = sys.getsizeof(request)

        print(f"\nTTSRequest size: {size} bytes")

        # Should be reasonably small
        assert size < 1000, "TTSRequest should be < 1KB"

    def test_bulk_request_memory(self) -> None:
        """Test memory usage for bulk request creation."""
        import sys

        requests = []
        for i in range(1000):
            requests.append(TTSRequest(
                text=f"Test message {i}",
                voice_id="test-voice",
                provider="azure",
            ))

        # Get total size (approximate)
        total_size = sum(sys.getsizeof(r) for r in requests)
        avg_size = total_size / len(requests)

        print(f"\n1000 requests total size: {total_size / 1024:.2f} KB")
        print(f"Average request size: {avg_size:.2f} bytes")

        # Should scale linearly without memory leaks
        assert total_size < 1024 * 1024, "1000 requests should be < 1MB"


# Performance thresholds for CI/CD
PERFORMANCE_THRESHOLDS = {
    "request_creation_mean_ms": 1.0,
    "request_creation_throughput": 1000,
    "validation_5000_chars_mean_ms": 5.0,
    "concurrent_10_requests_mean_ms": 10.0,
    "special_chars_mean_ms": 2.0,
}


def check_performance_regression(results: dict[str, BenchmarkResult]) -> list[str]:
    """Check for performance regressions against thresholds.

    Returns:
        List of regression warnings
    """
    warnings = []

    for name, threshold in PERFORMANCE_THRESHOLDS.items():
        if name.endswith("_throughput"):
            # Throughput should be above threshold
            base_name = name.replace("_throughput", "")
            if base_name in results and results[base_name].throughput_per_second < threshold:
                warnings.append(
                    f"Throughput regression: {base_name} "
                    f"({results[base_name].throughput_per_second:.2f} < {threshold})"
                )
        elif name.endswith("_mean_ms"):
            # Mean time should be below threshold
            base_name = name.replace("_mean_ms", "")
            if base_name in results and results[base_name].mean_time_ms > threshold:
                warnings.append(
                    f"Latency regression: {base_name} "
                    f"({results[base_name].mean_time_ms:.2f} > {threshold})"
                )

    return warnings
