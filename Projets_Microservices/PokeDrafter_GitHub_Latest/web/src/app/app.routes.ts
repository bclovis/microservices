import { Routes } from '@angular/router';
import { LoginComponent } from './features/auth/login/login.component';
import { RegisterComponent } from './features/auth/register/register.component';
import { DashboardLayoutComponent } from './features/dashboard/dashboard-layout/dashboard-layout.component';


export const routes: Routes = [
    { path: '', redirectTo: 'auth/login', pathMatch: 'full' },
    { path: 'auth/login', component: LoginComponent },
    { path: 'auth/register', component: RegisterComponent },
    { 
        path: 'dashboard', 
        component: DashboardLayoutComponent,
        children: [
            { path: '', redirectTo: 'play', pathMatch: 'full' },
            { path: 'teams', loadComponent: () => import('./features/teams/team-list/team-list.component').then(c => c.TeamListComponent) },
            { path: 'teams/build', loadComponent: () => import('./features/teams/team-builder/team-builder.component').then(c => c.TeamBuilderComponent) },
            { path: 'dex', loadComponent: () => import('./features/pokedex/pokedex-list/pokedex-list.component').then(c => c.PokedexListComponent) },
            { path: 'play', loadComponent: () => import('./features/battle/battle-arena/battle-arena.component').then(c => c.BattleArenaComponent) }
        ]
    }
];
