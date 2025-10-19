"""Simple examples of using the three Gemini tools."""
import asyncio
from server.services.gemini import analyze_text, analyze_image, analyze_video


async def main():
    # TEXT
    print("TEXT EXAMPLE:")
    result = await analyze_text("Pothole on Market St at 5th Ave")
    print(result, "\n")

    # IMAGE
    print("IMAGE EXAMPLE:")
    # result = await analyze_image("path/to/image.jpg", text="Market Street")
    # print(result, "\n")
    print("Uncomment and provide real image path\n")

    # VIDEO
    print("VIDEO EXAMPLE:")
    # result = await analyze_video("path/to/video.mp4")
    # print(result, "\n")
    print("Uncomment and provide real video path\n")


if __name__ == "__main__":
    asyncio.run(main())
