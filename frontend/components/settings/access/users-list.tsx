"use client";

import { Trash2, UserCheck, UserX, Loader2 } from "lucide-react";
import { useState } from "react";
import { Button } from "@/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
} from "@/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/ui/table";
import { useUsersListViewModel } from "@/hooks/view/use-users-list-view-model";
import type { User } from "@/services/auth";

interface UsersListProps {
  initialUsers?: User[];
}

export function UsersList({ initialUsers }: UsersListProps) {
  const { users, loading, error, handleDelete } =
    useUsersListViewModel(initialUsers);
  const [userToDelete, setUserToDelete] = useState<number | null>(null);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground bg-muted/50 rounded-xl border border-border">
        <Loader2 className="w-5 h-5 animate-spin mr-3 text-primary" />
        Carregando lista de usuários...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-sm text-destructive bg-destructive/10 rounded-lg border border-destructive/20 flex items-center gap-2">
        <UserX className="w-4 h-4" />
        {error}
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
      <Table>
        <TableHeader className="bg-muted/50">
          <TableRow>
            <TableHead className="w-[200px] px-6">Nome</TableHead>
            <TableHead className="px-6">Email</TableHead>
            <TableHead className="px-6">Função</TableHead>
            <TableHead className="px-6">Status</TableHead>
            <TableHead className="text-right px-6">Ações</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {users.map((user) => (
            <TableRow key={user.id} className="hover:bg-muted/50">
              <TableCell className="font-medium px-6 text-card-foreground">
                {user.name || "Sem Nome"}
              </TableCell>
              <TableCell className="px-6">{user.email}</TableCell>
              <TableCell className="px-6">
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium border ${
                    user.role === "admin"
                      ? "bg-purple-100 text-purple-700 border-purple-200 dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-800"
                      : "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800"
                  }`}
                >
                  {user.role}
                </span>
              </TableCell>
              <TableCell className="px-6">
                {user.is_active ? (
                  <span className="flex items-center text-emerald-600 dark:text-emerald-400 gap-1.5 font-medium text-xs">
                    <UserCheck className="w-3.5 h-3.5" /> Ativo
                  </span>
                ) : (
                  <span className="flex items-center text-destructive gap-1.5 font-medium text-xs">
                    <UserX className="w-3.5 h-3.5" /> Inativo
                  </span>
                )}
              </TableCell>
              <TableCell className="text-right px-6">
                <Dialog>
                  <DialogTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-muted-foreground hover:text-rose-600 hover:bg-rose-50 h-8 w-8 rounded-full"
                      title="Remover usuário"
                      onClick={() => setUserToDelete(user.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Confirmar exclusão</DialogTitle>
                      <DialogDescription>
                        Tem certeza que deseja remover o usuário{" "}
                        <strong>{user.name || user.email}</strong>? Essa ação
                        não pode ser desfeita.
                      </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                      <DialogClose asChild>
                        <Button variant="outline">Cancelar</Button>
                      </DialogClose>
                      <DialogClose asChild>
                        <Button
                          variant="destructive"
                          onClick={() => {
                            if (userToDelete) {
                              handleDelete(userToDelete);
                              setUserToDelete(null);
                            }
                          }}
                        >
                          Excluir
                        </Button>
                      </DialogClose>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </TableCell>
            </TableRow>
          ))}
          {users.length === 0 && (
            <TableRow>
              <TableCell
                colSpan={6}
                className="h-24 text-center text-slate-400"
              >
                Nenhum usuário encontrado.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
