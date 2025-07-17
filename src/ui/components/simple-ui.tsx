"use client";
import "./index.css";
import { useStream } from "@langchain/langgraph-sdk/react";
import { uiMessageReducer } from "@langchain/langgraph-sdk/react-ui";

interface SimpleUIProps {
    toolCallId: string;
    message: string;
    title?: string;
    timestamp?: string;
}

export default function SimpleUI(props: SimpleUIProps) {
    const { message, title = "Simple UI", timestamp } = props;

    const { thread, values } = useStream({
        apiUrl: "http://localhost:2024",
        assistantId: "agent",
    });

    return (
        <div className="flex flex-col w-full max-w-2xl border-[1px] rounded-xl border-blue-200 bg-blue-50 overflow-hidden">
            <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-2xl font-semibold text-blue-900">{title}</h2>
                    {timestamp && (
                        <span className="text-sm text-blue-600">{timestamp}</span>
                    )}
                </div>
                <div className="prose prose-blue max-w-none">
                    <p className="text-lg text-blue-800 leading-relaxed">
                        {message}
                    </p>
                </div>
            </div>
        </div>
    );
}
