/* The GTK 3 probe: a module any GTK 3 application loads (GTK_MODULES), which writes what GTK computed.
 *
 * build/gtk.py --screen compiles it, starts the application on a virtual display with GTK_MODULES pointing at
 * it and GTK_DEBUG=interactive (without which GTK keeps no record of which rule set a value), and sends SIGUSR1.
 * On the signal the probe writes, for every mapped toplevel: its type, title and size; every CSS node under it
 * with the style GTK computed for it and the stylesheet line each value came from
 * (gtk_style_context_to_string); and every mapped widget's type, CSS path and allocation in window
 * coordinates, so a value can be found on the photograph. SIGUSR2 walks each widget through the states a
 * pointer would put it in (prelight, active, checked, selected, disabled, backdrop), writes the same record for
 * each, and puts every widget back.
 *
 * Output: $REMAINDER_PROBE_OUT (a file; appended, one record per signal, each ending in a line "%%end").
 * GPL-3.0-or-later, as build/ is. AUTHORITY.md is the authority; this only reads.
 */
#include <gtk/gtk.h>
#include <glib-unix.h>
#include <stdio.h>
#include <string.h>

static FILE *out;
static const gchar *out_path;

static void
widget_line (GtkWidget *w, GtkWidget *top, int depth)
{
  GtkAllocation a;
  int x = 0, y = 0;
  gchar *path;

  if (!gtk_widget_get_mapped (w))
    return;
  gtk_widget_get_allocation (w, &a);
  gtk_widget_translate_coordinates (w, top, 0, 0, &x, &y);
  path = gtk_widget_path_to_string (gtk_widget_get_path (w));
  fprintf (out, "W %d %s %d %d %d %d %u %s\n", depth, G_OBJECT_TYPE_NAME (w), x, y, a.width, a.height,
           (unsigned) gtk_widget_get_state_flags (w), path);
  g_free (path);
}

static void walk (GtkWidget *w, GtkWidget *top, int depth);

static void
walk_child (GtkWidget *child, gpointer data)
{
  GtkWidget **pair = data;
  walk (child, pair[0], GPOINTER_TO_INT (pair[1]));
}

static void
walk (GtkWidget *w, GtkWidget *top, int depth)
{
  widget_line (w, top, depth);
  if (GTK_IS_CONTAINER (w))
    {
      gpointer pair[2] = { top, GINT_TO_POINTER (depth + 1) };
      gtk_container_forall (GTK_CONTAINER (w), walk_child, pair);
    }
}

static void
dump (const char *label)
{
  GList *tops, *l;

  out = fopen (out_path, "a");
  if (!out)
    return;
  fprintf (out, "%%%%record %s %s\n", label, g_get_prgname () ? g_get_prgname () : "?");
  tops = gtk_window_list_toplevels ();
  for (l = tops; l; l = l->next)
    {
      GtkWidget *top = l->data;
      GtkStyleContext *ctx;
      gchar *css;
      int wx = 0, wy = 0;

      if (!gtk_widget_get_mapped (top))
        continue;
      if (g_str_has_prefix (G_OBJECT_TYPE_NAME (top), "GtkInspector"))
        continue;
      if (gtk_widget_get_window (top))
        gdk_window_get_origin (gtk_widget_get_window (top), &wx, &wy);
      fprintf (out, "%%%%window %s %d %d %d %d %s\n", G_OBJECT_TYPE_NAME (top), wx, wy,
               gtk_widget_get_allocated_width (top), gtk_widget_get_allocated_height (top),
               GTK_IS_WINDOW (top) && gtk_window_get_title (GTK_WINDOW (top)) ?
               gtk_window_get_title (GTK_WINDOW (top)) : "");
      walk (top, top, 0);
      ctx = gtk_widget_get_style_context (top);
      css = gtk_style_context_to_string (ctx, GTK_STYLE_CONTEXT_PRINT_RECURSE | GTK_STYLE_CONTEXT_PRINT_SHOW_STYLE);
      fprintf (out, "%%%%css\n%s%%%%endcss\n", css);
      g_free (css);
    }
  g_list_free (tops);
  fprintf (out, "%%%%end\n");
  fclose (out);
}

static gboolean
on_usr1 (gpointer data)
{
  dump ("rest");
  return G_SOURCE_CONTINUE;
}

/* Each widget through each state: set the flag, let GTK restyle, record the widget's own nodes, put it back. */
static const struct { GtkStateFlags flag; const char *name; } STATES[] = {
  { GTK_STATE_FLAG_PRELIGHT, "hover" }, { GTK_STATE_FLAG_ACTIVE, "active" },
  { GTK_STATE_FLAG_CHECKED, "checked" }, { GTK_STATE_FLAG_SELECTED, "selected" },
  { GTK_STATE_FLAG_INSENSITIVE, "disabled" },
};

static void
states_of (GtkWidget *w, GtkWidget *top, int depth)
{
  guint i;
  if (!gtk_widget_get_mapped (w))
    return;
  for (i = 0; i < G_N_ELEMENTS (STATES); i++)
    {
      GtkStateFlags before = gtk_widget_get_state_flags (w);
      gchar *css;
      if (before & STATES[i].flag)
        continue;
      gtk_widget_set_state_flags (w, STATES[i].flag, FALSE);
      css = gtk_style_context_to_string (gtk_widget_get_style_context (w),
                                         GTK_STYLE_CONTEXT_PRINT_RECURSE | GTK_STYLE_CONTEXT_PRINT_SHOW_STYLE);
      if (strlen (css) > 24000)
        {
          /* A large container: its own node only. Its children are walked in their own right, and only
           * :disabled and :backdrop reach them from here. */
          g_free (css);
          css = gtk_style_context_to_string (gtk_widget_get_style_context (w), GTK_STYLE_CONTEXT_PRINT_SHOW_STYLE);
        }
      fprintf (out, "%%%%state %s\n", STATES[i].name);
      widget_line (w, top, depth);
      fprintf (out, "%%%%css\n%s%%%%endcss\n", css);
      g_free (css);
      gtk_widget_set_state_flags (w, before, TRUE);
    }
  if (GTK_IS_CONTAINER (w))
    {
      GList *kids = gtk_container_get_children (GTK_CONTAINER (w)), *k;
      for (k = kids; k; k = k->next)
        states_of (k->data, top, depth + 1);
      g_list_free (kids);
    }
}

static gboolean
on_usr2 (gpointer data)
{
  GList *tops, *l;
  out = fopen (out_path, "a");
  if (!out)
    return G_SOURCE_CONTINUE;
  fprintf (out, "%%%%record states %s\n", g_get_prgname () ? g_get_prgname () : "?");
  tops = gtk_window_list_toplevels ();
  for (l = tops; l; l = l->next)
    {
      GtkWidget *top = l->data;
      if (!gtk_widget_get_mapped (top) || g_str_has_prefix (G_OBJECT_TYPE_NAME (top), "GtkInspector"))
        continue;
      fprintf (out, "%%%%window %s 0 0 %d %d %s\n", G_OBJECT_TYPE_NAME (top), gtk_widget_get_allocated_width (top),
               gtk_widget_get_allocated_height (top), GTK_IS_WINDOW (top) && gtk_window_get_title (GTK_WINDOW (top))
               ? gtk_window_get_title (GTK_WINDOW (top)) : "");
      states_of (top, top, 0);
      {
        /* The window as it is when it is not key: GTK propagates :backdrop from the toplevel to every node. */
        GtkStateFlags before = gtk_widget_get_state_flags (top);
        gchar *css;
        gtk_widget_set_state_flags (top, GTK_STATE_FLAG_BACKDROP, FALSE);
        css = gtk_style_context_to_string (gtk_widget_get_style_context (top),
                                           GTK_STYLE_CONTEXT_PRINT_RECURSE | GTK_STYLE_CONTEXT_PRINT_SHOW_STYLE);
        fprintf (out, "%%%%state backdrop\n");
        widget_line (top, top, 0);
        fprintf (out, "%%%%css\n%s%%%%endcss\n", css);
        g_free (css);
        gtk_widget_set_state_flags (top, before, TRUE);
      }
    }
  g_list_free (tops);
  fprintf (out, "%%%%end\n");
  fclose (out);
  return G_SOURCE_CONTINUE;
}

/* GTK_DEBUG=interactive opens the inspector with the first window; it is only wanted for the record it makes GTK
 * keep, so it is hidden as soon as it appears. */
static gboolean
hide_inspector (gpointer data)
{
  GList *tops = gtk_window_list_toplevels (), *l;
  for (l = tops; l; l = l->next)
    if (g_str_has_prefix (G_OBJECT_TYPE_NAME (l->data), "GtkInspector") && gtk_widget_get_visible (l->data))
      gtk_widget_hide (l->data);
  g_list_free (tops);
  return G_SOURCE_CONTINUE;
}

G_MODULE_EXPORT void
gtk_module_init (gint *argc, gchar ***argv)
{
  out_path = g_getenv ("REMAINDER_PROBE_OUT");
  if (!out_path)
    return;
  g_unix_signal_add (SIGUSR1, on_usr1, NULL);
  g_unix_signal_add (SIGUSR2, on_usr2, NULL);
  g_timeout_add (250, hide_inspector, NULL);
}
