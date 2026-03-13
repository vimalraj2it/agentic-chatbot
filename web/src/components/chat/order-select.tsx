"use client";

import React from "react";
import { Check, Package, Calendar, User } from "lucide-react";
import { cn } from "@/lib/utils";

export interface OrderOption {
    id: string;
    item: string;
    date: string;
    status: string;
    customer?: string;
}

interface OrderSelectProps {
    orders: OrderOption[];
    onSelect: (orderId: string) => void;
    selectedId?: string;
}

export const OrderSelect = ({ orders, onSelect, selectedId }: OrderSelectProps) => {
    return (
        <div className="flex flex-col gap-3 my-4 p-4 border border-border rounded-2xl bg-card/50 backdrop-blur-sm shadow-sm">
            <h3 className="text-sm font-bold flex items-center gap-2 mb-1 px-1">
                <Package size={16} className="text-primary" />
                Select an Order to Proceed
            </h3>
            <div className="grid grid-cols-1 gap-2">
                {orders.map((order) => {
                    const isSelected = selectedId === order.id;
                    return (
                        <button
                            key={order.id}
                            onClick={() => onSelect(order.id)}
                            className={cn(
                                "flex items-center justify-between p-3 rounded-xl border transition-all text-left group",
                                isSelected
                                    ? "border-primary bg-primary/5 ring-1 ring-primary"
                                    : "border-border bg-background hover:border-primary/50 hover:bg-muted/50"
                            )}
                        >
                            <div className="flex flex-col gap-1">
                                <div className="flex items-center gap-2">
                                    <span className="text-sm font-bold text-foreground group-hover:text-primary transition-colors">
                                        {order.item}
                                    </span>
                                    <span className={cn(
                                        "text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider",
                                        order.status === "Delivered" ? "bg-emerald-500/10 text-emerald-600" : "bg-amber-500/10 text-amber-600"
                                    )}>
                                        {order.status}
                                    </span>
                                </div>
                                <div className="flex items-center gap-4 text-[11px] text-muted-foreground">
                                    <div className="flex items-center gap-1">
                                        <Calendar size={12} />
                                        {order.date}
                                    </div>
                                    {order.customer && (
                                        <div className="flex items-center gap-1">
                                            <User size={12} />
                                            {order.customer}
                                        </div>
                                    )}
                                </div>
                            </div>
                            <div className={cn(
                                "w-6 h-6 rounded-full border flex items-center justify-center transition-all",
                                isSelected ? "bg-primary border-primary text-primary-foreground" : "border-border bg-muted/20"
                            )}>
                                {isSelected && <Check size={14} strokeWidth={3} />}
                            </div>
                        </button>
                    );
                })}
            </div>
            <p className="text-[10px] text-muted-foreground px-1 mt-1 font-medium italic">
                Click an order to select it and resume the workflow.
            </p>
        </div>
    );
};
